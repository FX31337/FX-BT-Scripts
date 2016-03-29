#!/usr/bin/env python3

import argparse
import sys
import os
import csv
import re
from struct import pack
import time
import datetime
import mmap

class Input:
    def __init__(self, path):
        if args.verbose:
            print('[INFO] Trying to read data from %s...' % path)
        try:
            self.path = open(path, 'r')
        except OSError as e:
            print("[ERROR] '%s' raised when tried to read the file '%s'" % (e.strerror, e.filename))
            sys.exit(1)

    def __del__(self):
        self.path.close()

    def _addBar(self, barTimestamp, tickTimestamp, open, high, low, close, volume):
        self.uniBars += [{
            'barTimestamp': barTimestamp,
           'tickTimestamp': tickTimestamp,
                    'open': open,
                    'high': high,
                     'low': low,
                   'close': close,
                  'volume': volume
        }]

def string_to_timestamp(s):
    return datetime.datetime(
            int(s[0:4]),   # Year
            int(s[5:7]),   # Month
            int(s[8:10]),  # Day
            int(s[11:13]), # Hour
            int(s[14:16]), # Minute
            int(s[17:19]), # Second
            int(s[20:]),   # Microseconds
            datetime.timezone.utc)

class CSV(Input):
    def __init__(self, path):
        super().__init__(path)

        self._map_obj = mmap.mmap(self.path.fileno(), 0,
                flags=mmap.MAP_SHARED,
                prot=mmap.PROT_READ)

    def __iter__(self):
        return self

    def __next__(self):
        line = self._map_obj.readline()
        if line:
            return self._parseLine(line)
        else:
            raise StopIteration

    def _parseLine(self, line):
        tick = line.split(b',')
        return {
            # Storing timestamp as float to preserve its precision.
            # 'timestamp': time.mktime(datetime.datetime.strptime(tick[0], '%Y.%m.%d %H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc).timetuple()),
            'timestamp': string_to_timestamp(tick[0]).timestamp(),
             'bidPrice': float(tick[1]),
             'askPrice': float(tick[2]),
            'bidVolume': float(tick[3]),
            'askVolume': float(tick[4])               # float() handles ending '\n' character
        }

class Output:
    def __init__(self, timeframe, path):
        self.deltaTimestamp = timeframe*60
        self.endTimestamp = None
        self.barCount = 0

        try:
            os.remove(path)  # Remove existing output file before creating an appended new one
        except (OSError, IOError) as e:
            pass
        try:
            self.path = open(path, 'ab')
        except OSError as e:
            print("[ERROR] '%s' raised when tried to open for appending the file '%s'" % (e.strerror, e.filename))
            sys.exit(1)


    def __del__(self):
        self.path.close()

    def _aggregate(self, tick):
        if not self.endTimestamp or tick['timestamp'] >= self.endTimestamp:
            uniBar = None
            if self.endTimestamp: uniBar = {
                'barTimestamp': self.startTimestamp,
               'tickTimestamp': tick['timestamp'],
                        'open': self.open,
                        'high': self.high,
                         'low': self.low,
                       'close': self.close,
                      'volume': self.volume
            }

            self.startTimestamp = (int(tick['timestamp'])//self.deltaTimestamp)*self.deltaTimestamp
            self.endTimestamp = self.startTimestamp + self.deltaTimestamp
            self.open = self.high = self.low = self.close = tick['bidPrice']
            self.volume = tick['bidVolume'] + tick['askVolume']

            if uniBar: return (uniBar, True)
        else:
            self.high = max(tick['bidPrice'], self.high)
            self.low  = min(tick['bidPrice'], self.low)
            self.close = tick['bidPrice']
            self.volume += tick['bidVolume'] + tick['askVolume']

        uniBar = {
            'barTimestamp': self.startTimestamp,
           'tickTimestamp': tick['timestamp'],
                    'open': self.open,
                    'high': self.high,
                     'low': self.low,
                   'close': self.close,
                  'volume': self.volume
        }
        return (uniBar, False)


    def _aggregateWithTicks(self, tick):
        if not self.endTimestamp or tick['timestamp'] >= self.endTimestamp:
            self.startTimestamp = (int(tick['timestamp'])//self.deltaTimestamp)*self.deltaTimestamp
            self.endTimestamp = self.startTimestamp + self.deltaTimestamp
            self.open = self.high = self.low = tick['bidPrice']
            self.volume = tick['bidVolume'] + tick['askVolume']
            self.barCount += 1
        else:
            self.high = max(tick['bidPrice'], self.high)
            self.low  = min(tick['bidPrice'], self.low)
            self.volume += tick['bidVolume'] + tick['askVolume']

        return {
            'barTimestamp': self.startTimestamp,
           'tickTimestamp': tick['timestamp'],
                    'open': self.open,
                    'high': self.high,
                     'low': self.low,
                   'close': tick['bidPrice'],
                  'volume': self.volume
        }


class HST509(Output):
    def __init__(self, ticks, path, timeframe, symbol):
        # Initialize variables in parent constructor
        super().__init__(timeframe, path)
        bars = bytearray()

    def flush(self):
        # Build header (148 Bytes in total)
        header = bytearray()
        header += pack('<i', 400)                                                    # Version
        header += bytearray('(C)opyright 2003, MetaQuotes Software Corp.'.ljust(64,  # Copyright
                            '\x00'),'latin1', 'ignore')
        header += bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')            # Symbol
        header += pack('<i', timeframe)                                              # Period
        header += pack('<i', 5)                                                      # Digits, using the default value of HST format
        header += pack('<i', int(time.time()))                                       # Time of sign (database creation)
        header += pack('<i', 0)                                                      # Time of last synchronization
        header += bytearray(13*4)                                                    # Space for future use

        self.path.write(header)
        self.path.write(bars)

    def pack_tick(self, tick):
        (uniBar, newUniBar) = self._aggregate(tick)
        if newUniBar:
            bars += self._packUniBar(uniBar)

    def _packUniBar(self, uniBar):
        bar = bytearray()
        bar += pack('<i', uniBar['barTimestamp'])      # Time
        bar += pack('<d', uniBar['open'])              # Open
        bar += pack('<d', uniBar['low'])               # Low
        bar += pack('<d', uniBar['high'])              # High
        bar += pack('<d', uniBar['close'])             # Close
        bar += pack('<d', max(uniBar['volume'], 1.0))  # Volume

        return bar


class HST574(Output):
    def __init__(self, ticks, path, timeframe, symbol):
        # Initialize variables in parent constructor
        super().__init__(timeframe, path)
        bars = bytearray()

    def pack_tick(self, tick):
        # Transform universal bar list to binary bar data (60 Bytes per bar)
        (uniBar, newUniBar) = self._aggregate(tick)
        if newUniBar:
            bars += self._packUniBar(uniBar)

    def flush(self):
        # Build header (148 Bytes in total)
        header = bytearray()
        header += pack('<i', 401)                                                    # Version
        header += bytearray('(C)opyright 2003, MetaQuotes Software Corp.'.ljust(64,  # Copyright
                            '\x00'),'latin1', 'ignore')
        header += bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')            # Symbol
        header += pack('<i', timeframe)                                              # Period
        header += pack('<i', 5)                                                      # Digits, using the default value of HST format
        header += pack('<i', int(time.time()))                                       # Time of sign (database creation)
        header += pack('<i', 0)                                                      # Time of last synchronization
        header += bytearray(13*4)                                                    # Space for future use

        self.path.write(header)
        self.path.write(bars)

    def _packUniBar(self, uniBar):
        bar = bytearray()
        bar += pack('<i', uniBar['barTimestamp'])           # Time
        bar += bytearray(4)                                 # Add 4 bytes of padding.
        # OHLCV values.
        bar += pack('<d', uniBar['open'])                   # Open
        bar += pack('<d', uniBar['high'])                   # High
        bar += pack('<d', uniBar['low'])                    # Low
        bar += pack('<d', uniBar['close'])                  # Close
        bar += pack('<Q', max(round(uniBar['volume']), 1))  # Volume
        bar += pack('<i', 0)                                # Spread
        bar += pack('<Q', 0)                                # Real volume

        return bar


class FXT(Output):
    def pack_tick(self, tick):
        # Transform universal bar list to binary bar data (56 Bytes per bar)
        for tick in ticks:
            uniBar = self._aggregateWithTicks(tick)
            if not firstUniBar: firstUniBar = uniBar             # Store first and ...
            lastUniBar = uniBar                                  # ... last bar data for header.
            bars += pack('<iiddddQii',
                    int(uniBar['barTimestamp']),                                 # Bar datetime.
                    0,                                                           # Add 4 bytes of padding.
                    uniBar['open'],uniBar['high'],uniBar['low'],uniBar['close'], # OHLCV values.
                    max(round(uniBar['volume']), 1),                             # Volume (documentation says it's a double, though it's stored as a long int).
                    int(uniBar['tickTimestamp']),                                # The current time within a bar.
                    4)                                                           # Flag to launch an expert (0 - bar will be modified, but the expert will not be launched).

    def __init__(self, ticks, path, timeframe, server, symbol, spread):
        # Initialize variables in parent constructor.
        super().__init__(timeframe, path)
        bars = bytearray()
        firstUniBar = lastUniBar = None

    def flush():
        # Build header (728 Bytes in total)
        header = bytearray()
        header += pack('<i', 405)                                                       # FXT header version: 405
        header += bytearray('Copyright 2001-2015, MetaQuotes Software Corp.'.ljust(64,  # Copyright
                            '\x00'), 'latin1', 'ignore')
        header += bytearray(server.ljust(128, '\x00'), 'latin1', 'ignore')              # Account server name.
        header += bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')               # Symbol pair.
        header += pack('<i', timeframe)                                                 # Period of data aggregation in minutes (timeframe).
        header += pack('<i', 0)                                                         # Model type: 0 - every tick, 1 - control points, 2 - bar open.
        header += pack('<i', self.barCount)                                             # Bars - amount of bars in history.
        header += pack('<i', int(firstUniBar['barTimestamp']))                          # Modelling start date - date of the first tick.
        header += pack('<i', int(lastUniBar['barTimestamp']))                           # Modelling end date - date of the last tick.
        header += bytearray(4)                                                          # Add 4 bytes of padding. This potentially can be totalTicks.
        header += pack('<d', 99.9)                                                      # Modeling quality (max. 99.9).
        # General parameters
        header += bytearray('EUR'.ljust(12, '\x00'), 'latin1', 'ignore')                # Base currency (12 bytes).
        header += pack('<i', spread)                                                    # Spread in points.
        header += pack('<i', 5)                                                         # Digits, using the default value of FXT format
        header += bytearray(4)                                                          # Add 4 bytes of padding.
        header += pack('<d', 1e-5)                                                      # Point size (e.g. 0.00001).
        header += pack('<i', 1)                                                         # Minimal lot size in centi lots (hundredths).
        header += pack('<i', 50000)                                                     # Maximal lot size in centi lots (hundredths).
        header += pack('<i', 1)                                                         # Lot step in centi lots (hundredths).
        header += pack('<i', 0)                                                         # Stops level value (orders stop distance in points).
        header += pack('<i', 0)                                                         # GTC (Good till cancel) - instruction to close pending orders at end of day (default: False).
        header += bytearray(4)                                                          # Add 4 bytes of padding.
        # Profit Calculation parameters
        header += pack('<d', 100000.0)                                                  # ContractSize - contract size
        header += pack('<d', 0.0)                                                       # Tick value in quote currency (empty).
        header += pack('<d', 0.0)                                                       # Size of one tick (empty).
        header += pack('<i', 0)                                                         # Profit calculation mode: 0 - Forex, 1 - CFD, 2 - Futures.
        # Swap calculation
        header += pack('<i', 1)                                                         # Enable swap (default: True).
        header += pack('<i', 0)                                                         # Swap calculation method: 0 - in points, 1 - in the symbol base currency, 2 - by interest, 3 - in the margin currency.
        header += bytearray(4)                                                          # Add 4 bytes of padding.
        header += pack('<d', 0.0)                                                       # Swap of the buy order - long overnight swap value.
        header += pack('<d', 0.0)                                                       # Swap of the sell order - short overnight swap value.
        header += pack('<i', 3)                                                         # Day of week to charge 3 days swap rollover. Default: WEDNESDAY (3).
        # Margin calculation
        header += pack('<i', 100)                                                       # Account leverage (default: 100).
        header += pack('<i', 1)                                                         # Free margin calculation mode {MARGIN_DONT_USE, MARGIN_USE_ALL, MARGIN_USE_PROFIT, MARGIN_USE_LOSS}
        header += pack('<i', 0)                                                         # Margin calculation mode: 0 - Forex, 1 - CFD, 2 - Futures, 3 - CFD for indexes.
        header += pack('<i', 30)                                                        # Margin stopout level (default: 30).
        header += pack('<i', 0)                                                         # Margin stop out check mode {MARGIN_TYPE_PERCENT, MARGIN_TYPE_CURRENCY}
        header += pack('<d', 0.0)                                                       # Margin requirements.
        header += pack('<d', 0.0)                                                       # Margin maintenance requirements.
        header += pack('<d', 0.0)                                                       # Margin requirements for hedged positions.
        header += pack('<d', 1.0)                                                       # Margin divider used for leverage calculation.
        header += bytearray('EUR'.ljust(12, '\x00'), 'latin1', 'ignore')                # Margin currency.
        header += bytearray(4)                                                          # Padding space - add 4 bytes to align the next double.
        # Commission calculation
        header += pack('<d', 0.0)                                                       # Basic commission.
        header += pack('<i', 0)                                                         # Basic commission type {COMM_TYPE_MONEY, COMM_TYPE_PIPS, COMM_TYPE_PERCENT}
        header += pack('<i', 0)                                                         # Commission per lot or per deal {COMMISSION_PER_LOT, COMMISSION_PER_DEAL}
        # For internal use
        header += pack('<i', 0)                                                         # Index of the first bar at which modeling started (0 for the first bar).
        header += pack('<i', 0)                                                         # Index of the last bar at which modeling started (0 for the last bar).
        header += pack('<i', 0)                                                         # Bar index where modeling started using M1 bars (0 for the first bar).
        header += pack('<i', 0)                                                         # Bar index where modeling started using M5 bars (0 for the first bar).
        header += pack('<i', 0)                                                         # Bar index where modeling started using M15 bars (0 for the first bar).
        header += pack('<i', 0)                                                         # Bar index where modeling started using M30 bars (0 for the first bar).
        header += pack('<i', 0)                                                         # Bar index where modeling started using H1 bars (0 for the first bar).
        header += pack('<i', 0)                                                         # Bar index where modeling started using H4 bars (0 for the first bar).
        header += pack('<i', 0)                                                         # Begin date from tester settings (must be zero).
        header += pack('<i', 0)                                                         # End date from tester settings (must be zero).
        header += pack('<i', 0)                                                         # Order's freeze level in points.
        header += pack('<i', 0)                                                         # Number of errors during model generation which needs to be fixed before testing.
        header += bytearray(60*4)                                                       # Reserved - Space for future use

        self.path.write(header)
        self.path.write(bars)

def _hstFilename(symbol, timeframe):
    return '%s%d.hst' % (symbol, timeframe)

def _fxtFilename(symbol, timeframe):
    return '%s%d_0.fxt' % (symbol, timeframe)

if __name__ == '__main__':
    # Parse the arguments
    argumentParser = argparse.ArgumentParser(add_help=False)
    argumentParser.add_argument('-i', '--input-file',
        action='store',      dest='inputFile', help='input file', default=None, required=True)
    argumentParser.add_argument('-f', '--output-format',
        action='store',      dest='outputFormat', help='format of output file (FXT/HST/Old HST), as: fxt4/hst4/hst4_509', default='fxt4')
    argumentParser.add_argument('-s', '--symbol',
        action='store',      dest='symbol', help='symbol code (maximum 12 characters)', default='EURUSD')
    argumentParser.add_argument('-t', '--timeframe',
        action='store',      dest='timeframe', help='one of the timeframe values: M1, M5, M15, M30, H1, H4, D1, W1, MN', default='M1')
    argumentParser.add_argument('-p', '--spread',
        action='store',      dest='spread', help='spread value in points', default=20)
    argumentParser.add_argument('-d', '--output-dir',
        action='store',      dest='outputDir', help='destination directory to save the output file', default='.')
    argumentParser.add_argument('-S', '--server',
        action='store',      dest='server', help='name of FX server', default='default')
    argumentParser.add_argument('-v', '--verbose',
        action='store_true', dest='verbose', help='increase output verbosity')
    argumentParser.add_argument('-h', '--help',
        action='help', help='Show this help message and exit')
    args = argumentParser.parse_args()

    # Checking input file argument
    if args.verbose:
        print('[INFO] Input file: %s' % args.inputFile)

    # Checking symbol argument
    if len(args.symbol) > 12:
        print('[WARNING] Symbol is more than 12 characters, cutting its end off!')
        symbol = args.symbol[0:12]
    else:
        symbol = args.symbol
    if args.verbose:
        print('[INFO] Symbol name: %s' % symbol)

    # Converting timeframe argument to minutes
    timeframe_list = []
    timeframe_conv = {
            'm1': 1, 'm5':  5, 'm15': 15, 'm30':  30,
            'h1':60, 'h4':240, 'd1':1440, 'w1':10080, 'mn':43200
    }

    for arg in args.timeframe.lower().split(','):
        if arg in timeframe_conv:
            timeframe_list.append(timeframe_conv[arg])
        else:
            print('[ERROR] Bad timeframe setting \'{}\'!'.format(arg))
            sys.exit(1)

    if args.verbose:
        print('[INFO] Timeframe: %s - %s minute(s)' % (args.timeframe.upper(), timeframe_list))

    # Checking spread argument
    spread = int(args.spread)
    if args.verbose:
        print('[INFO] Spread: %d' % spread)

    # Create output directory
    os.makedirs(args.outputDir, 0o755, True)
    if args.verbose:
        print('[INFO] Output directory: %s' % args.outputDir)

    # Checking server argument
    if len(args.server) > 128:
        print('[WARNING] Server name is longer than 128 characters, cutting its end off!')
        server = args.server[0:128]
    else:
        server = args.server
    if args.verbose:
        print('[INFO] Server name: %s' % server)

    outputFormat = args.outputFormat.lower()
    if args.verbose:
        print('[INFO] Output format: %s' % outputFormat)

    multiple_timeframes = len(timeframe_list) > 1

    # Reading input file, creating intermediate format for future input sources other than CSV
    obj = []

    for timeframe in timeframe_list:
        # Checking output file format argument and doing conversion
        if outputFormat == 'hst4_509':
            outputPath = os.path.join(args.outputDir, _hstFilename(symbol, timeframe))
            o = HST509(None, outputPath, timeframe, symbol)
        elif outputFormat == 'hst4':
            outputPath = os.path.join(args.outputDir, _hstFilename(symbol, timeframe))
            o = HST574(None, outputPath, timeframe, symbol)
        elif outputFormat == 'fxt4':
            outputPath = os.path.join(args.outputDir, _fxtFilename(symbol, timeframe))
            o = FXT(None, outputPath, timeframe, server, symbol, spread)
        else:
            print('[ERROR] Unknown output file format!')
            sys.exit(1)

        obj.append(o)

    try:
        for tick in CSV(args.inputFile):
            map(lambda x: x.pack_tick(tick), obj)

        map(lambda x: x.flush(), obj)
    except KeyboardInterrupt as e:
        print('\nExiting by user request...')
        sys.exit()

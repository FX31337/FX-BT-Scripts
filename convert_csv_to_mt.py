#!/usr/bin/env python3

import argparse
import sys
import os
import csv
import re
from struct import *
import time
import datetime

class Input:
    def __init__(self, fileName):
        if args.verbose:
            print('[INFO] Trying to read data from %s...' % fileName)
        try:
            with open(fileName, 'r') as inputFile:
                self.ticks = inputFile.read().splitlines()
        except OSError as e:
            print("[ERROR] '%s' raised when tried to read the file '%s'" % (e.strerror, e.filename))
            sys.exit(1)


    def aggregate(self):
        self.uniBars = []
        deltaTimestamp = timeframe*60
        endTimestamp = None

        for tick in self.ticks:
            currentTimestamp = tick['timestamp']
            if not endTimestamp or currentTimestamp >= endTimestamp:
                if endTimestamp:
                    self._addBar(startTimestamp, currentTimestamp, open, high, low, close, volume)

                startTimestamp = (int(tick['timestamp'])//deltaTimestamp)*deltaTimestamp
                endTimestamp = startTimestamp + deltaTimestamp
                open = high = low = close = tick['bidPrice']
                volume = tick['bidVolume'] + tick['askVolume']
            else:
                high = max(tick['bidPrice'], high)
                low  = min(tick['bidPrice'], low)
                close = tick['bidPrice']
                volume += tick['bidVolume'] + tick['askVolume']

        self._addBar(startTimestamp, currentTimestamp, open, high, low, close, volume)


    def aggregateWithTicks(self):
        self.uniBars = []
        deltaTimestamp = timeframe*60
        endTimestamp = None
        self.barCount = 0

        for tick in self.ticks:
            currentTimestamp = tick['timestamp']
            if not endTimestamp or currentTimestamp >= endTimestamp:
                startTimestamp = (int(tick['timestamp'])//deltaTimestamp)*deltaTimestamp
                endTimestamp = startTimestamp + deltaTimestamp
                open = high = low = tick['bidPrice']
                volume = tick['bidVolume'] + tick['askVolume']

                self._addBar(startTimestamp, currentTimestamp, open, high, low, tick['bidPrice'], volume)
                self.barCount += 1
            else:
                high = max(tick['bidPrice'], high)
                low  = min(tick['bidPrice'], low)
                volume += tick['bidVolume'] + tick['askVolume']

                self._addBar(startTimestamp, currentTimestamp, open, high, low, tick['bidPrice'], volume)


    def _addBar(self, barTimestamp, tickTimestamp, open, high, low, close, volume):
        self.uniBars += [{'barTimestamp': barTimestamp,
                          'tickTimestamp': tickTimestamp,
                          'open': open,
                          'high': high,
                          'low': low,
                          'close': close,
                          'volume': volume
                        }]


class CSV(Input):
    def parse(self):
        self.ticks = csv.reader(self.ticks, delimiter=',')

        uniTicks = []
        for tick in self.ticks:
            uniTicks += [{'timestamp': datetime.datetime.strptime(tick[0], '%Y.%m.%d %H:%M:%S.%f').replace(tzinfo=datetime.timezone.utc).timestamp(),
                          'bidPrice' : float(tick[1]),
                          'askPrice' : float(tick[2]),
                          'bidVolume': float(tick[3]),
                          'askVolume': float(tick[4])
                        }]

        self.ticks = uniTicks


class Output:
    def _write(self, content, filename):
        try:
            with open(filename, 'wb') as o:
                o.write(content)
        except OSError as e:
            print("[ERROR] '%s' raised when tried to save the file '%s'" % (e.strerror, e.filename))
            sys.exit(1)


class HST509(Output):
    def __init__(self, uniBars, outputPath):
        # Build header (148 Bytes in total)
        header = bytearray()
        header += pack('<i', 400)                                                       # Version
        header += bytearray('(C)opyright 2003, MetaQuotes Software Corp.'.ljust(64,     # Copyright
                            '\x00'),'latin1', 'ignore')
        header += bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')               # Symbol
        header += pack('<i', timeframe)                                                 # Period
        header += pack('<i', 5)                                                         # Digits, using the default value of HST format
        header += pack('<i', int(time.time()))                                          # Time of sign (database creation)
        header += pack('<i', 0)                                                         # Time of last synchronization
        header += bytearray(13*4)                                                       # Space for future use

        # Transform universal bar list to binary bar data (44 Bytes per bar)
        bars = bytearray()
        for uniBar in uniBars:
            bars += pack('<i', uniBar['barTimestamp'])      # Time
            bars += pack('<d', uniBar['open'])              # Open
            bars += pack('<d', uniBar['low'])               # Low
            bars += pack('<d', uniBar['high'])              # High
            bars += pack('<d', uniBar['close'])             # Close
            bars += pack('<d', max(uniBar['volume'], 1.0))  # Volume

        self._write(header + bars, outputPath)


class HST574(Output):
    def __init__(self, uniBars, outputPath):
        # Build header (148 Bytes in total)
        header = bytearray()
        header += pack('<i', 401)                                                       # Version
        header += bytearray('(C)opyright 2003, MetaQuotes Software Corp.'.ljust(64,     # Copyright
                            '\x00'),'latin1', 'ignore')
        header += bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')               # Symbol
        header += pack('<i', timeframe)                                                 # Period
        header += pack('<i', 5)                                                         # Digits, using the default value of HST format
        header += pack('<i', int(time.time()))                                          # Time of sign (database creation)
        header += pack('<i', 0)                                                         # Time of last synchronization
        header += bytearray(13*4)                                                       # Space for future use

        # Transform universal bar list to binary bar data (60 Bytes per bar)
        bars = bytearray()
        for uniBar in uniBars:
            bars += pack('<i', uniBar['barTimestamp'])          # Time
            bars += bytearray(4)                                # 4 Bytes of padding
            bars += pack('<d', uniBar['open'])                  # Open
            bars += pack('<d', uniBar['high'])                  # High
            bars += pack('<d', uniBar['low'])                   # Low
            bars += pack('<d', uniBar['close'])                 # Close
            bars += pack('<Q', max(round(uniBar['volume']), 1)) # Volume
            bars += pack('<i', 0)                               # Spread
            bars += pack('<Q', 0)                               # Real volume

        self._write(header + bars, outputPath)


class FXT(Output):
    def __init__(self, uniBars, barCount, outputPath):
        # Build header (728 Bytes in total)
        header = bytearray()
        header += pack('<i', 405)                                                       # Version
        header += bytearray('Copyright 2001-2015, MetaQuotes Software Corp.'.ljust(64,  # Copyright
                            '\x00'), 'latin1', 'ignore')
        header += bytearray(server.ljust(128, '\x00'), 'latin1', 'ignore')              # Server
        header += bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')               # Symbol
        header += pack('<i', 1)                                                         # Period is set statically to 1, since we're generating an ``every tick'' file
        header += pack('<i', 0)                                                         # Model - for what modeling type was the ticks sequence generated, 0 means ``every tick model''
        header += pack('<i', barCount)                                                  # Bars - Amount bars in history
        header += pack('<i', self._timestamp(uniBars[0]))                               # FromDate - Date of first tick
        header += pack('<i', self._timestamp(uniBars[-1]))                              # ToDate - Date of last tick
        header += bytearray(4)                                                          # 4 Bytes of padding
        header += pack('<d', 99.9)                                                      # ModelQuality - modeling quality
        # General parameters
        header += bytearray('EUR'.ljust(12, '\x00'), 'latin1', 'ignore')                # Currency - currency base
        header += pack('<i', spread)                                                    # Spread in pips
        header += pack('<i', 5)                                                         # Digits, using the default value of FXT format
        header += bytearray(4)                                                          # 4 Bytes of padding
        header += pack('<d', 1e-5)                                                      # Point
        header += pack('<i', 1)                                                         # LotMin - minimum lot
        header += pack('<i', 50000)                                                     # LotMax - maximum lot
        header += pack('<i', 1)                                                         # LotStep
        header += pack('<i', 0)                                                         # StopsLevel - stops level value
        header += pack('<i', 1)                                                         # GtcPendings - instruction to close pending orders at the end of day, true by default
        header += bytearray(4)                                                          # 4 Bytes of padding
        # Profit Calculation parameters
        header += pack('<d', 100000.0)                                                  # ContractSize - contract size
        header += pack('<d', 0.0)                                                       # TickValue - value of one tick
        header += pack('<d', 0.0)                                                       # TickSize - size of one tick
        header += pack('<i', 0)                                                         # ProfitMode - profit calculation mode {PROFIT_CALC_FOREX, PROFIT_CALC_CFD, PROFIT_CALC_FUTURES}
        # Swap calculation
        header += pack('<i', 0)                                                         # SwapEnable - enable swap, true by default
        header += pack('<i', 0)                                                         # SwapType - type of swap {SWAP_BY_POINTS, SWAP_BY_DOLLARS, SWAP_BY_INTEREST}
        header += bytearray(4)                                                          # 4 Bytes of padding
        header += pack('<d', 0.0)                                                       # SwapLong
        header += pack('<d', 0.0)                                                       # SwapShort - swap overnight value
        header += pack('<i', 2)                                                         # SwapRolloverThreeDays - three-days swap rollover
        # Margin calculation
        header += pack('<i', 100)                                                       # Leverage, 100 by default
        header += pack('<i', 1)                                                         # FreeMarginMode - free margin calculation mode {MARGIN_DONT_USE, MARGIN_USE_ALL, MARGIN_USE_PROFIT, MARGIN_USE_LOSS}
        header += pack('<i', 0)                                                         # MarginMode - margin calculation mode {MARGIN_CALC_FOREX,MARGIN_CALC_CFD,MARGIN_CALC_FUTURES,MARGIN_CALC_CFDINDEX}
        header += pack('<i', 100)                                                       # MarginStopout - margin stopout level
        header += pack('<i', 0)                                                         # MarginStopoutMode - stop out check mode {MARGIN_TYPE_PERCENT, MARGIN_TYPE_CURRENCY}
        header += pack('<d', 100000.0)                                                  # MarginInitial - margin requirements
        header += pack('<d', 100000.0)                                                  # MarginMaintenance - margin maintenance requirements
        header += pack('<d', 50000.0)                                                   # MarginHedged - margin requirements for hedged positions
        header += pack('<d', 1.25)                                                      # MarginDivider
        header += bytearray('EUR'.ljust(12, '\x00'), 'latin1', 'ignore')                # MarginCurrency
        header += bytearray(4)                                                          # 4 Bytes of padding
        # Commission calculation
        header += pack('<d', 0.0)                                                       # CommissionBase - basic commission
        header += pack('<i', 1)                                                         # CommissionType - basic commission type {COMM_TYPE_MONEY, COMM_TYPE_PIPS, COMM_TYPE_PERCENT}
        header += pack('<i', 0)                                                         # CommissionLots - commission per lot or per deal {COMMISSION_PER_LOT, COMMISSION_PER_DEAL}
        # For internal use
        header += pack('<i', 0)                                                         # FromBar - FromDate bar number
        header += pack('<i', 0)                                                         # ToBar - ToDate bar number
        header += pack('<6i', 1, 0, 0, 0, 0, 0)                                         # StartPeriod - number of bar at which the smaller period modeling started
        header += pack('<i', 0)                                                         # SetFrom - begin date from tester settings
        header += pack('<i', 0)                                                         # SetTo - end date from tester settings
        header += pack('<i', 0)                                                         # FreezeLevel - order's freeze level in points
        header += bytearray(61*4)                                                       # Reserved - Space for future use

        # Transform universal bar list to binary bar data (56 Bytes per bar)
        bars = bytearray()
        for uniBar in uniBars:
            bars += pack('<i', self._timestamp(uniBar))         # Time
            bars += bytearray(4)                                # 4 Bytes of padding
            bars += pack('<d', uniBar['open'])                  # Open
            bars += pack('<d', uniBar['high'])                  # High
            bars += pack('<d', uniBar['low'])                   # Low
            bars += pack('<d', uniBar['close'])                 # Close
            bars += pack('<Q', max(round(uniBar['volume']), 1)) # Volume (Document says it's a double, though it's stored as a long int.)
            bars += pack('<i', int(uniBar['tickTimestamp']))    # Current time within a bar
            bars += pack('<i', 4)                               # Flag to launch an expert

        self._write(header + bars, outputPath)


    def _timestamp(self, tick):
        return int(tick['barTimestamp'])


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
        action='store',      dest='spread', help='spread value in pips', default=20)
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
    timeframe = args.timeframe.lower()
    if timeframe == 'm1':
        timeframe = 1
    elif timeframe == 'm5':
        timeframe = 5
    elif timeframe == 'm15':
        timeframe = 15
    elif timeframe == 'm30':
        timeframe = 30
    elif timeframe == 'h1':
        timeframe = 60
    elif timeframe == 'h4':
        timeframe = 240
    elif timeframe == 'd1':
        timeframe = 1440
    elif timeframe == 'w1':
        timeframe = 10080
    elif timeframe == 'mn':
        timeframe = 43200
    else:
        print('[ERROR] Bad timeframe setting!')
        sys.exit(1)
    if args.verbose:
        print('[INFO] Timeframe: %s - %d minute(s)' % (args.timeframe.upper(), timeframe))

    # Checking spread argument
    spread = int(args.spread)
    if args.verbose:
        print('[INFO] Spread: %d' % spread)

    # Checking output directory
    outputDir = args.outputDir
    if outputDir[-1] != '/':
        outputDir += '/'
    os.makedirs(outputDir, 0o755, True)
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

    # Reading input file, creating intermediate format for future input sources other than CSV
    try:
        csvInput = CSV(args.inputFile)
        csvInput.parse()

        # Checking output file format argument and doing conversion
        outputFormat = args.outputFormat.lower()
        if outputFormat == 'hst4_509':
            csvInput.aggregate()
            HST509(csvInput.uniBars, outputDir + _hstFilename(symbol, timeframe))
        elif outputFormat == 'hst4':
            csvInput.aggregate()
            HST574(csvInput.uniBars, outputDir + _hstFilename(symbol, timeframe))
        elif outputFormat == 'fxt4':
            csvInput.aggregateWithTicks()
            FXT(csvInput.uniBars, csvInput.barCount, outputDir + _fxtFilename(symbol, timeframe))
        else:
            print('[ERROR] Unknown output file format!')
            sys.exit(1)
        if args.verbose:
            print('[INFO] Output format: %s' % outputFormat)
    except KeyboardInterrupt as e:
        print('\nExiting by user request...')
        sys.exit()

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
    def __init__(self, inputFile):
        if args.verbose:
            print('[INFO] Trying to read data from %s...' % inputFile)
        try:
            with open(inputFile, 'r') as i:
                self.rawInput = i.read()
        except OSError as e:
            print("ERROR: %s raised when tried to save the file '%s'" % (e.strerror, e.filename))
            sys.exit(1)

    def _aggregate(self, rawRows, timeframe):
        uniBars = []
        deltaTime = datetime.timedelta(0, timeframe)
        barTime = None
        startTime = None
        endTime = None
        aggregatedOpen = 0.0
        aggregatedLow = 0.0
        aggregatedHigh = 0.0
        aggregatedClose = 0.0
        aggregatedVolume = 0.0

        for rawRow in rawRows:
            timestamp = re.split('[. :]', rawRow[0])  # Convert date & time in the rawRow to a list
            currentTime = datetime.datetime(int(timestamp[0]), int(timestamp[1]), int(timestamp[2]), int(timestamp[3]), int(timestamp[4]), int(timestamp[5]), 1000*int(timestamp[6])) 
            bidPrice = float(rawRow[1])
            askPrice = float(rawRow[2])
            bidVolume = float(rawRow[3])
            askVolume = float(rawRow[4])
            if not endTime or currentTime >= endTime:
                # Append aggregated rows to uniBars list
                if endTime:
                    uniBars.append([barTime, aggregatedOpen, aggregatedLow, aggregatedHigh, aggregatedClose, aggregatedVolume])
                # Initialize values for the first or next bar
                barTime = currentTime
                startTime = datetime.datetime(int(timestamp[0]), int(timestamp[1]), int(timestamp[2]), int(timestamp[3]), int(timestamp[4]))
                endTime = startTime + deltaTime
                # Low is the lowest bid, High is the highest ask, Volume is the bid volume TODO ?
                aggregatedOpen = aggregatedClose = aggregatedLow = bidPrice
                aggregatedHigh = askPrice
                aggregatedVolume = bidVolume
            else:
                # Commulate lines belong to a bar
                aggregatedClose = bidPrice
                aggregatedVolume += bidVolume
                if bidPrice < aggregatedLow:
                    aggregatedLow = bidPrice
                if askPrice > aggregatedHigh:
                    aggregatedHigh = askPrice

        uniBars.append([barTime, aggregatedOpen, aggregatedLow, aggregatedHigh, aggregatedClose, aggregatedVolume])
        return uniBars


class CSV(Input):
    def parse(self, timeframe):
        rawRows = csv.reader(self.rawInput.splitlines(), delimiter=',')
        return self._aggregate(rawRows, timeframe)


class Output:
    def _write(self, content, filename):
        with open(filename, 'wb') as o:
            o.write(content)


class HST509(Output):
    def __init__(self, uniBars, outputPath):
        # Build header (148 Bytes in total)
        binVersion   = pack('<i', 400)
        binCopyright = bytearray('(C)opyright 2003, MetaQuotes Software Corp.'.ljust(64, '\x00'), 'latin1', 'ignore')
        binSymbol    = bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')
        binPeriod    = pack('<i', timeframe)
        binDigits    = pack('<i', 5)                        # Default value of HST format
        binTimeSign  = pack('<i', int(time.time()))         # Time of creation
        binLastSync  = pack('<i', 0)
        binUnused    = bytearray(13*4)
        header = binVersion + binCopyright + binSymbol + binPeriod + binDigits + binTimeSign + binLastSync + binUnused

        # Transform universal bar list to binary bar data (44 Bytes per bar)
        bars = bytearray()
        for uniBar in uniBars:
            bars += pack('<i', int(uniBar[0].timestamp()))  # Time
            bars += pack('<d', uniBar[1])                   # Open
            bars += pack('<d', uniBar[2])                   # Low
            bars += pack('<d', uniBar[3])                   # High
            bars += pack('<d', uniBar[4])                   # Close
            bars += pack('<d', uniBar[5])                   # Volume

        self._write(header + bars, outputPath)


class HST574(Output):
    def __init__(self, uniBars, outputPath):
        # Build header (148 Bytes in total)
        binVersion   = pack('<i', 401)
        binCopyright = bytearray('(C)opyright 2003, MetaQuotes Software Corp.'.ljust(64, '\x00'), 'latin1', 'ignore')
        binSymbol    = bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')
        binPeriod    = pack('<i', timeframe)
        binDigits    = pack('<i', 5)                    # Default value of HST format
        binTimeSign  = pack('<i', int(time.time()))     # Time of creation
        binLastSync  = pack('<i', 0)
        binUnused    = bytearray(13*4)
        header = binVersion + binCopyright + binSymbol + binPeriod + binDigits + binTimeSign + binLastSync + binUnused

        # Transform universal bar list to binary bar data (60 Bytes per bar)
        bars = bytearray()
        for uniBar in uniBars:
            bars += pack('<d', uniBar[0].timestamp())                   # Time
            bars += pack('<d', uniBar[1])                               # Open
            bars += pack('<d', uniBar[3])                               # High
            bars += pack('<d', uniBar[2])                               # Low
            bars += pack('<d', uniBar[4])                               # Close
            bars += pack('<Q', int(uniBar[5]*1e6))                      # Volume TODO ?
            bars += pack('<i', round((uniBar[3]) - uniBar[2])*10000)    # Spread TODO ?
            bars += pack('<Q', int(uniBar[5]*1e6))                      # Real volume TODO ?

        self._write(header + bars, outputPath)


class FXT(Output):
    def __init__(self, uniBars, spread, outputPath):
        # Build header (148 Bytes in total)
        binVersion      = pack('<i', 403)
        binCopyright    = bytearray('Copyright 2001-2015, MetaQuotes Software Corp.'.ljust(64, '\x00'), 'latin1', 'ignore')
        binSymbol       = bytearray(symbol.ljust(12, '\x00'), 'latin1', 'ignore')
        binPeriod       = pack('<i', timeframe)
        binModel        = pack('<i', 0)     # TODO ?
        binBars         = pack('<i', len(uniBars))
        binFromDate     = pack('<i', int(uniBars[0][0].timestamp()))
        binToDate       = pack('<i', int(uniBars[1][0].timestamp()))
        binModelQuality = pack('<d', 0)     # TODO ?
        # General parameters
        binCurrency    = bytearray(''[0:12].ljust(12, '\x00'), 'latin1', 'ignore')  # TODO ?
        binSpread      = pack('<i', spread) # TODO ?
        binDigits      = pack('<i', 5)      # TODO Default value of FXT format
        binPoint       = pack('<d', 0)      # TODO ?
        binLotMin      = pack('<i', 0)      # TODO ?
        binLotMax      = pack('<i', 0)      # TODO ?
        binLotStep     = pack('<i', 0)      # TODO ?
        binStopsLevel  = pack('<i', 0)      # TODO ?
        binGtcPendings = pack('<i', 0)      # TODO ?
        # Profit Calculation parameters
        binContractSize = pack('<d', 0)     # TODO ?
        binTickValue    = pack('<d', 0)     # TODO ?
        binTickSize     = pack('<d', 0)     # TODO ?
        binProfitMode   = pack('<d', 0)     # TODO ?
        # Swap calculation
        binSwapEnable = pack('<i', 0)       # TODO ?
        binSwapType   = pack('<i', 0)       # TODO ?
        binSwapLong   = pack('<d', 0)       # TODO ?
        binSwapShort  = pack('<d', 0)       # TODO ?
        binSwap3days  = pack('<i', 0)       # TODO ?
        # Margin calculation
        binLeverage          = pack('<i', 0)    # TODO ?
        binFreeMarginMode    = pack('<i', 0)    # TODO ?
        binMarginMode        = pack('<i', 0)    # TODO ?
        binMarginStopOut     = pack('<i', 0)    # TODO ?
        binMarginStopOutMode = pack('<i', 0)    # TODO ?
        binMarginInitial     = pack('<d', 0)    # TODO ?
        binMarginMaintenance = pack('<d', 0)    # TODO ?
        binMarginHedged      = pack('<d', 0)    # TODO ?
        binMarginDivider     = pack('<d', 0)    # TODO ?
        binMarginCurrency    = bytearray(''[0:12].ljust(12, '\x00'), 'latin1', 'ignore')    # TODO ?
        # Commission calculation
        binCommissionBase = pack('<d', 0)   # TODO ?
        binCommissionType = pack('<i', 0)   # TODO ?
        binCommissionLots = pack('<i', 0)   # TODO ?
        # For internal use
        binFromBar     = pack('<i', 0)      # TODO ?
        binToBar       = pack('<i', 0)      # TODO ?
        binStartPeriod = bytearray(6*4)     # TODO ?
        binSetFrom     = pack('<i', 0)      # TODO ?
        binSetTo       = pack('<i', 0)      # TODO ?
        binReserved    = bytearray(62*4)    # TODO ?
        header = binVersion + binCopyright + binSymbol + binPeriod + binModel + binBars + binFromDate + binToDate + binModelQuality + \
                 binCurrency + binSpread + binDigits + binPoint + binLotMin + binLotMax + binLotStep + binStopsLevel + binGtcPendings + \
                 binContractSize + binTickValue + binTickSize + binProfitMode + \
                 binSwapEnable + binSwapType + binSwapLong + binSwapShort + binSwap3days + \
                 binLeverage + binFreeMarginMode + binMarginMode + binMarginStopOut + binMarginStopOutMode + binMarginInitial + binMarginMaintenance + binMarginHedged + binMarginDivider + binMarginCurrency + \
                 binCommissionBase + binCommissionType + binCommissionLots + \
                 binFromBar + binStartPeriod + binSetFrom + binSetTo + binReserved

        # Transform universal bar list to binary bar data (60 Bytes per bar)
        bars = bytearray()
        for uniBar in uniBars:
            bars += pack('<i', int(uniBar[0].timestamp()))  # Time
            bars += pack('<d', uniBar[1])                   # Open
            bars += pack('<d', uniBar[2])                   # Low
            bars += pack('<d', uniBar[3])                   # High
            bars += pack('<d', uniBar[4])                   # Close
            bars += pack('<d', uniBar[5])                   # Volume
            bars += pack('<i', int(uniBar[0].timestamp()))  # Current time within a bar TODO ?
            bars += pack('<i', 0)                           # Flag to launch an expert TODO ?

        self._write(header + bars, outputPath)


def _hstFilename(symbol, timeframe):
    return '%s%d.hst' % (symbol, timeframe//60)

def _fxtFilename(symbol, timeframe):
    return '%s%d_0.fxt' % (symbol, timeframe//60)

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
        action='store',      dest='timeframe', help='one of the timeframe values: M1, M5, M15, M30, H1, H4, D1', default='M1')
    argumentParser.add_argument('-p', '--spread',
        action='store',      dest='spread', help='spread value in pips', default=1)
    argumentParser.add_argument('-d', '--output-dir',
        action='store',      dest='outputDir', help='destination directory to save the output file', default='.')
    argumentParser.add_argument('-v', '--verbose',
        action='store_true', dest='verbose', help='increase output verbosity')
    argumentParser.add_argument('-h', '--help',
        action='help', help='Show this help message and exit')
    args = argumentParser.parse_args()

    # Checking input file argument
    if not args.inputFile:
        print('ERROR: You haven\'t specified an input file!')
        sys.exit(1)
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

    # Converting timeframe argument to seconds
    timeframe = args.timeframe.lower()
    if timeframe == 'm1':
        timeframe = 60
    elif timeframe == 'm5':
        timeframe = 300
    elif timeframe == 'm15':
        timeframe = 900
    elif timeframe == 'm30':
        timeframe = 1800
    elif timeframe == 'h1':
        timeframe = 3600
    elif timeframe == 'h4':
        timeframe = 14400
    elif timeframe == 'd1':
        timeframe = 86400
    else:
        print('ERROR: Bad timeframe setting!')
        sys.exit(1)
    if args.verbose:
        print('[INFO] Timeframe: %s (%d seconds)' % (args.timeframe.upper(), timeframe))

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
        print('[INFO] Output directgory: %s' % args.outputDir)

    # Reading input file, creating intermediate format for future input sources other than CSV
    uniRows = CSV(args.inputFile).parse(timeframe)

    # Checking output file format argument and doing conversion
    outputFormat = args.outputFormat.lower()
    if outputFormat == 'fxt4':
        #FXT(uniRows, symbol, timeframe, spread)
        FXT(uniRows, spread, outputDir + _fxtFilename(symbol, timeframe))
    elif outputFormat == 'hst4':
        #HST574(uniRows, symbol, timeframe)
        HST574(uniRows, outputDir + _hstFilename(symbol, timeframe))
    elif outputFormat == 'hst4_509':
        #HST509(uniRows, symbol, timeframe)
        HST509(uniRows, outputDir + _hstFilename(symbol, timeframe))
    else:
        print('ERROR: Unknown output file format!')
        sys.exit(1)
    if args.verbose:
        print('[INFO] Output format: %s' % outputFormat)

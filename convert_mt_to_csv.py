#!/usr/bin/env python3

import argparse
import sys
from struct import *
import datetime
import csv
import math

class Input:
    def __init__(self, fileName):
        if args.verbose:
            print('[INFO] Trying to read data from %s...' % fileName)
        try:
            with open(fileName, 'rb') as inputFile:
                self.content = inputFile.read()
        except OSError as e:
            print("[ERROR] '%s' raised when tried to read the file '%s'" % (e.strerror, e.fileName))
            sys.exit(1)

        self._checkFormat()
        self.numberOfRows = (len(self.content) - self.headerLength)//self.rowLength
        self._parse()


    def _checkFormat(self):
        if (len(self.content) - self.headerLength)%self.rowLength != 0:
            print('[ERROR] File length isn\'t suitable for this kind of format!')
            sys.exit(1)

        if self.version != unpack('<i', self.content[0:4])[0]:
            print('[ERROR] Unsupported format version!')
            sys.exit(1)


    def _parse(self):
        pass


class HST4_509(Input):
    version = 400
    headerLength = 148
    rowLength = 44

    def _parse(self):
        self.rows = []
        for i in range(0, self.numberOfRows):
            base = self.headerLength + i*self.rowLength
            self.rows += [{'timestamp': datetime.datetime.fromtimestamp(
                                        unpack('<i', self.content[base          :base + 4      ])[0], datetime.timezone.utc),
                           'open'     : unpack('<d', self.content[base +       4:base + 4 +   8])[0],
                           'low'      : unpack('<d', self.content[base + 4 +   8:base + 4 + 2*8])[0],
                           'high'     : unpack('<d', self.content[base + 4 + 2*8:base + 4 + 3*8])[0],
                           'close'    : unpack('<d', self.content[base + 4 + 3*8:base + 4 + 4*8])[0],
                           'volume'   : unpack('<d', self.content[base + 4 + 4*8:base + 4 + 5*8])[0]
                         }]


    def __str__(self):
        table = ''
        separator = ','
        for row in self.rows:
            table += '{:<19}'.format('{:%Y.%m.%d %H:%M:%S}'.format(row['timestamp']))
            table += separator
            table += '{:>9.5f}'.format(row['open'])
            table += separator
            table += '{:>9.5f}'.format(row['high'])
            table += separator
            table += '{:>9.5f}'.format(row['low'])
            table += separator
            table += '{:>9.5f}'.format(row['close'])
            table += separator
            table += '{:>12.2f}'.format(row['volume'])
            table += '\n'
        return table[:-1]


    def toCsv(self, fileName):
        with open(fileName, 'w', newline='') as csvFile:
            writer = csv.writer(csvFile, quoting = csv.QUOTE_NONE)
            for row in self.rows:
                writer.writerow(['{:%Y.%m.%d %H:%M:%S}'.format(row['timestamp']),
                                 '{:.5f}'.format(row['open']),
                                 '{:.5f}'.format(row['high']),
                                 '{:.5f}'.format(row['low']),
                                 '{:.5f}'.format(row['close']),
                                 '{:.2f}'.format(row['volume'])
                               ])


class HST4(Input):
    version = 401
    headerLength = 148
    rowLength = 60

    def _parse(self):
        self.rows = []
        for i in range(0, self.numberOfRows):
            base = self.headerLength + i*self.rowLength
            self.rows += [{'timestamp' : datetime.datetime.fromtimestamp(
                                         unpack('<i', self.content[base          :base +       4])[0], datetime.timezone.utc),
                           'open'      : unpack('<d', self.content[base +       8:base +     2*8])[0],
                           'high'      : unpack('<d', self.content[base +     2*8:base +     3*8])[0],
                           'low'       : unpack('<d', self.content[base +     3*8:base +     4*8])[0],
                           'close'     : unpack('<d', self.content[base +     4*8:base +     5*8])[0],
                           'volume'    : unpack('<Q', self.content[base +     5*8:base +     6*8])[0],
                           'spread'    : unpack('<i', self.content[base +     6*8:base + 4 + 6*8])[0],
                           'realVolume': unpack('<Q', self.content[base + 4 + 6*8:base + 4 + 7*8])[0]
                         }]


    def __str__(self):
        table = ''
        separator = ','
        for row in self.rows:
            table += '{:<19}'.format('{:%Y.%m.%d %H:%M:%S}'.format(row['timestamp']))
            table += separator
            table += '{:>.5f}'.format(row['open'])
            table += separator
            table += '{:>.5f}'.format(row['high'])
            table += separator
            table += '{:>.5f}'.format(row['low'])
            table += separator
            table += '{:>.5f}'.format(row['close'])
            table += separator
            table += '{:>d}'.format(row['volume'])
            table += separator
            table += '{:>d}'.format(row['spread'])
            table += separator
            table += '{:>d}'.format(row['realVolume'])
            table += '\n'
        return table[:-1]


    def toCsv(self, fileName):
        with open(fileName, 'w', newline='') as csvFile:
            writer = csv.writer(csvFile, quoting = csv.QUOTE_NONE)
            for row in self.rows:
                writer.writerow(['{:%Y.%m.%d %H:%M:%S}'.format(row['timestamp']),
                                 '{:.5f}'.format(row['open']),
                                 '{:.5f}'.format(row['high']),
                                 '{:.5f}'.format(row['low']),
                                 '{:.5f}'.format(row['close']),
                                 '{:d}'.format(row['volume']),
                                 '{:d}'.format(row['spread']),
                                 '{:d}'.format(row['realVolume'])
                               ])


class FXT4(Input):
    version = 405
    headerLength = 728
    rowLength = 56

    def _parse(self):
        self.rows = []
        for i in range(0, self.numberOfRows):
            base = self.headerLength + i*self.rowLength
            self.rows += [{'barTimestamp' : datetime.datetime.fromtimestamp(
                                            unpack('<i', self.content[base          :base +       4])[0], datetime.timezone.utc),
                           'open'         : unpack('<d', self.content[base +       8:base +     2*8])[0],
                           'high'         : unpack('<d', self.content[base +     2*8:base +     3*8])[0],
                           'low'          : unpack('<d', self.content[base +     3*8:base +     4*8])[0],
                           'close'        : unpack('<d', self.content[base +     4*8:base +     5*8])[0],
                           'volume'       : unpack('<Q', self.content[base +     5*8:base +     6*8])[0],
                           'tickTimestamp': datetime.datetime.fromtimestamp(
                                            unpack('<i', self.content[base +     6*8:base + 4 + 6*8])[0], datetime.timezone.utc),
                           'flag'         : unpack('<i', self.content[base + 4 + 6*8:base +     7*8])[0]
                         }]


    def __str__(self):
        table = ''
        separator = ','
        for row in self.rows:
            table += '{:<19}'.format('{:%Y.%m.%d %H:%M:%S}'.format(row['barTimestamp']))
            table += separator
            table += '{:>.5f}'.format(row['open'])
            table += separator
            table += '{:>.5f}'.format(row['high'])
            table += separator
            table += '{:>.5f}'.format(row['low'])
            table += separator
            table += '{:>.5f}'.format(row['close'])
            table += separator
            table += '{:>d}'.format(row['volume'])
            table += separator
            table += '{:<19}'.format('{:%Y.%m.%d %H:%M:%S}'.format(row['tickTimestamp']))
            table += separator
            table += '{:>d}'.format(row['flag'])
            table += '\n'
        return table[:-1]


    def toCsv(self, fileName):
        with open(fileName, 'w', newline='') as csvFile:
            writer = csv.writer(csvFile, quoting = csv.QUOTE_NONE)
            for row in self.rows:
                writer.writerow(['{:%Y.%m.%d %H:%M:%S}'.format(row['barTimestamp']),
                                 '{:.5f}'.format(row['open']),
                                 '{:.5f}'.format(row['high']),
                                 '{:.5f}'.format(row['low']),
                                 '{:.5f}'.format(row['close']),
                                 '{:d}'.format(row['volume']),
                                 '{:%Y.%m.%d %H:%M:%S}'.format(row['tickTimestamp']),
                                 '{:d}'.format(row['flag'])
                               ])


if __name__ == '__main__':
    # Parse the arguments
    argumentParser = argparse.ArgumentParser(add_help=False)
    argumentParser.add_argument('-i', '--input-file', action='store', dest='inputFile', help='input file', required=True)
    argumentParser.add_argument('-f', '--input-format', action='store', dest='inputFormat', help='MetaTrader format of input file (fxt4/hst4/hst4_509)', required=True)
    argumentParser.add_argument('-o', '--output-file', action='store', dest='outputFile', help='output CSV file', default=None)
    argumentParser.add_argument('-v', '--verbose', action='store_true', dest='verbose', help='increase output verbosity')
    argumentParser.add_argument('-h', '--help', action='help', help='Show this help message and exit')
    args = argumentParser.parse_args()

    if args.inputFormat == 'hst4_509':
        hst_509 = HST4_509(args.inputFile)
        hst_509.toCsv(args.outputFile) if args.outputFile else print(hst_509)
    elif args.inputFormat == 'hst4':
        hst4 = HST4(args.inputFile)
        hst4.toCsv(args.outputFile) if args.outputFile else print(hst4)
    elif args.inputFormat == 'fxt4':
        fxt4 = FXT4(args.inputFile)
        fxt4.toCsv(args.outputFile) if args.outputFile else print(fxt4)
    else:
        print('[ERROR] Unknown input file format \'%s\'!' % args.inputFormat)
        sys.exit(1)

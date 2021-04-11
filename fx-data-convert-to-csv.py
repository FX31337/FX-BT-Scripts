#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import bstruct
import csv
import datetime
import math
import struct
import sys


class Input:
    def __init__(self, fileName):
        if args.verbose:
            print("[INFO] Trying to read data from %s..." % fileName)
        try:
            with open(fileName, "rb") as inputFile:
                self.content = inputFile.read()
        except OSError as e:
            print(
                "[ERROR] '%s' raised when tried to read the file '%s'"
                % (e.strerror, e.fileName)
            )
            sys.exit(1)

        self._checkFormat()
        if self.rowLength != 0:
            self.numberOfRows = (
                len(self.content) - self.headerLength
            ) // self.rowLength
        self._parse()

    def _checkFormat(self):
        if (len(self.content) - self.headerLength) % self.rowLength != 0:
            print("[ERROR] File length isn't valid for this kind of format!")

        if self.version != struct.unpack("<i", self.content[0:4])[0]:
            print("[ERROR] Unsupported format version!")
            sys.exit(1)

    def _parse(self):
        pass


class HCC(Input):
    rowLength = 0
    headerLength = 228
    version = 501

    def _checkFormat(self):
        header = HccHeader(self.content)

        if header.magic != 501:
            print("[ERROR] Unsupported format version!")
            sys.exit(1)

    def _parse(self):
        self.rows = []

        # Skip the header
        base = HccHeader._size

        # Consume all the tables
        while True:
            t = HccTable(self.content, base)

            if t.off == t.size == 0:
                break

            # Consume all the records
            rh = HccRecordHeader(self.content, t.off)
            assert rh.magic == 0x81

            # We have to keep track of the cursor as some records have various
            # trailing bytes
            row_base = t.off + HccRecordHeader._size
            for i in range(rh.rows):
                tick = HccRecord(self.content, row_base)

                assert tick.separator & 0x00088884 == 0x00088884

                self.rows += [
                    {
                        "timestamp": datetime.datetime.fromtimestamp(tick.time),
                        "open": tick.open,
                        "high": tick.high,
                        "low": tick.low,
                        "close": tick.close,
                    }
                ]

                row_base += HccRecord._size + (
                    ((tick.separator >> 28) & 15)
                    + ((tick.separator >> 24) & 15)
                    + ((tick.separator >> 20) & 15)
                )

            base += HccTable._size

    def __str__(self):
        table = ""
        separator = ","
        for row in self.rows:
            table += "{:<19}".format("{:%Y.%m.%d %H:%M:%S}".format(row["timestamp"]))
            table += separator
            table += "{:>9.5f}".format(row["open"])
            table += separator
            table += "{:>9.5f}".format(row["high"])
            table += separator
            table += "{:>9.5f}".format(row["low"])
            table += separator
            table += "{:>9.5f}".format(row["close"])
            table += "\n"
        return table[:-1]

    def toCsv(self, fileName):
        with open(fileName, "w", newline="") as csvFile:
            writer = csv.writer(csvFile, quoting=csv.QUOTE_NONE)
            for row in self.rows:
                writer.writerow(
                    [
                        "{:%Y.%m.%d %H:%M:%S}".format(row["timestamp"]),
                        "{:.5f}".format(row["open"]),
                        "{:.5f}".format(row["high"]),
                        "{:.5f}".format(row["low"]),
                        "{:.5f}".format(row["close"]),
                    ]
                )


class HST509(Input):
    version = 400
    headerLength = 148
    rowLength = 44

    def _parse(self):
        self.rows = []
        for i in range(0, self.numberOfRows):
            base = self.headerLength + i * self.rowLength
            self.rows += [
                {
                    "timestamp": datetime.datetime.fromtimestamp(
                        struct.unpack("<i", self.content[base : base + 4])[0],
                        datetime.timezone.utc,
                    ),
                    "open": struct.unpack("<d", self.content[base + 4 : base + 4 + 8])[
                        0
                    ],
                    "low": struct.unpack(
                        "<d", self.content[base + 4 + 8 : base + 4 + 2 * 8]
                    )[0],
                    "high": struct.unpack(
                        "<d", self.content[base + 4 + 2 * 8 : base + 4 + 3 * 8]
                    )[0],
                    "close": struct.unpack(
                        "<d", self.content[base + 4 + 3 * 8 : base + 4 + 4 * 8]
                    )[0],
                    "volume": struct.unpack(
                        "<d", self.content[base + 4 + 4 * 8 : base + 4 + 5 * 8]
                    )[0],
                }
            ]

    def __str__(self):
        table = ""
        separator = ","
        for row in self.rows:
            table += "{:<19}".format("{:%Y.%m.%d %H:%M:%S}".format(row["timestamp"]))
            table += separator
            table += "{:>9.5f}".format(row["open"])
            table += separator
            table += "{:>9.5f}".format(row["high"])
            table += separator
            table += "{:>9.5f}".format(row["low"])
            table += separator
            table += "{:>9.5f}".format(row["close"])
            table += separator
            table += "{:>12.2f}".format(row["volume"])
            table += "\n"
        return table[:-1]

    def toCsv(self, fileName):
        with open(fileName, "w", newline="") as csvFile:
            writer = csv.writer(csvFile, quoting=csv.QUOTE_NONE)
            for row in self.rows:
                writer.writerow(
                    [
                        "{:%Y.%m.%d %H:%M:%S}".format(row["timestamp"]),
                        "{:.5f}".format(row["open"]),
                        "{:.5f}".format(row["high"]),
                        "{:.5f}".format(row["low"]),
                        "{:.5f}".format(row["close"]),
                        "{:.2f}".format(row["volume"]),
                    ]
                )


class HST(Input):
    version = 401
    headerLength = 148
    rowLength = 60

    def _parse(self):
        self.rows = []
        for i in range(0, self.numberOfRows):
            base = self.headerLength + i * self.rowLength
            self.rows += [
                {
                    "timestamp": datetime.datetime.fromtimestamp(
                        struct.unpack("<i", self.content[base : base + 4])[0],
                        datetime.timezone.utc,
                    ),
                    "open": struct.unpack("<d", self.content[base + 8 : base + 2 * 8])[
                        0
                    ],
                    "high": struct.unpack(
                        "<d", self.content[base + 2 * 8 : base + 3 * 8]
                    )[0],
                    "low": struct.unpack(
                        "<d", self.content[base + 3 * 8 : base + 4 * 8]
                    )[0],
                    "close": struct.unpack(
                        "<d", self.content[base + 4 * 8 : base + 5 * 8]
                    )[0],
                    "volume": struct.unpack(
                        "<Q", self.content[base + 5 * 8 : base + 6 * 8]
                    )[0],
                    "spread": struct.unpack(
                        "<i", self.content[base + 6 * 8 : base + 4 + 6 * 8]
                    )[0],
                    "realVolume": struct.unpack(
                        "<Q", self.content[base + 4 + 6 * 8 : base + 4 + 7 * 8]
                    )[0],
                }
            ]

    def __str__(self):
        table = ""
        separator = ","
        for row in self.rows:
            table += "{:<19}".format("{:%Y.%m.%d %H:%M:%S}".format(row["timestamp"]))
            table += separator
            table += "{:>.5f}".format(row["open"])
            table += separator
            table += "{:>.5f}".format(row["high"])
            table += separator
            table += "{:>.5f}".format(row["low"])
            table += separator
            table += "{:>.5f}".format(row["close"])
            table += separator
            table += "{:>d}".format(row["volume"])
            table += separator
            table += "{:>d}".format(row["spread"])
            table += separator
            table += "{:>d}".format(row["realVolume"])
            table += "\n"
        return table[:-1]

    def toCsv(self, fileName):
        with open(fileName, "w", newline="") as csvFile:
            writer = csv.writer(csvFile, quoting=csv.QUOTE_NONE)
            for row in self.rows:
                writer.writerow(
                    [
                        "{:%Y.%m.%d %H:%M:%S}".format(row["timestamp"]),
                        "{:.5f}".format(row["open"]),
                        "{:.5f}".format(row["high"]),
                        "{:.5f}".format(row["low"]),
                        "{:.5f}".format(row["close"]),
                        "{:d}".format(row["volume"]),
                        "{:d}".format(row["spread"]),
                        "{:d}".format(row["realVolume"]),
                    ]
                )


class FXT(Input):
    version = 405
    headerLength = 728
    rowLength = 56

    def _parse(self):
        self.rows = []
        for i in range(0, self.numberOfRows):
            base = self.headerLength + i * self.rowLength
            self.rows += [
                {
                    "barTimestamp": datetime.datetime.fromtimestamp(
                        struct.unpack("<i", self.content[base : base + 4])[0],
                        datetime.timezone.utc,
                    ),
                    "open": struct.unpack("<d", self.content[base + 8 : base + 2 * 8])[
                        0
                    ],
                    "high": struct.unpack(
                        "<d", self.content[base + 2 * 8 : base + 3 * 8]
                    )[0],
                    "low": struct.unpack(
                        "<d", self.content[base + 3 * 8 : base + 4 * 8]
                    )[0],
                    "close": struct.unpack(
                        "<d", self.content[base + 4 * 8 : base + 5 * 8]
                    )[0],
                    "volume": struct.unpack(
                        "<Q", self.content[base + 5 * 8 : base + 6 * 8]
                    )[0],
                    "tickTimestamp": datetime.datetime.fromtimestamp(
                        struct.unpack(
                            "<i", self.content[base + 6 * 8 : base + 4 + 6 * 8]
                        )[0],
                        datetime.timezone.utc,
                    ),
                    "flag": struct.unpack(
                        "<i", self.content[base + 4 + 6 * 8 : base + 7 * 8]
                    )[0],
                }
            ]

    def __str__(self):
        table = ""
        separator = ","
        for row in self.rows:
            table += "{:<19}".format("{:%Y.%m.%d %H:%M:%S}".format(row["barTimestamp"]))
            table += separator
            table += "{:>.5f}".format(row["open"])
            table += separator
            table += "{:>.5f}".format(row["high"])
            table += separator
            table += "{:>.5f}".format(row["low"])
            table += separator
            table += "{:>.5f}".format(row["close"])
            table += separator
            table += "{:>d}".format(row["volume"])
            table += separator
            table += "{:<19}".format(
                "{:%Y.%m.%d %H:%M:%S}".format(row["tickTimestamp"])
            )
            table += separator
            table += "{:>d}".format(row["flag"])
            table += "\n"
        return table[:-1]

    def toCsv(self, fileName):
        with open(fileName, "w", newline="") as csvFile:
            writer = csv.writer(csvFile, quoting=csv.QUOTE_NONE)
            for row in self.rows:
                writer.writerow(
                    [
                        "{:%Y.%m.%d %H:%M:%S}".format(row["barTimestamp"]),
                        "{:.5f}".format(row["open"]),
                        "{:.5f}".format(row["high"]),
                        "{:.5f}".format(row["low"]),
                        "{:.5f}".format(row["close"]),
                        "{:d}".format(row["volume"]),
                        "{:%Y.%m.%d %H:%M:%S}".format(row["tickTimestamp"]),
                        "{:d}".format(row["flag"]),
                    ]
                )


if __name__ == "__main__":
    # Parse the arguments
    argumentParser = argparse.ArgumentParser(add_help=False)
    argumentParser.add_argument(
        "-i",
        "--input-file",
        action="store",
        dest="inputFile",
        help="Input file",
        required=True,
    )
    argumentParser.add_argument(
        "-f",
        "--input-format",
        action="store",
        dest="inputFormat",
        help="MetaTrader format of input file (fxt/hcc/hst/hst509)",
        required=True,
    )
    argumentParser.add_argument(
        "-o",
        "--output-file",
        action="store",
        dest="outputFile",
        help="Output CSV file",
        default=None,
    )
    argumentParser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="Enables verbose messages",
    )
    argumentParser.add_argument(
        "-D",
        "--debug",
        action="store_true",
        dest="debug",
        help="Enables debugging messages",
    )
    argumentParser.add_argument(
        "-h", "--help", action="help", help="Show this help message and exit"
    )
    args = argumentParser.parse_args()

    if args.inputFormat == "hst509":
        hst509 = HST509(args.inputFile)
        hst509.toCsv(args.outputFile) if args.outputFile else print(hst509)
    elif args.inputFormat == "hst":
        hst = HST(args.inputFile)
        hst.toCsv(args.outputFile) if args.outputFile else print(hst)
    elif args.inputFormat == "fxt":
        fxt = FXT(args.inputFile)
        fxt.toCsv(args.outputFile) if args.outputFile else print(fxt)
    elif args.inputFormat == "hcc":
        hcc = HCC(args.inputFile)
        hcc.toCsv(args.outputFile) if args.outputFile else print(hcc)
    else:
        print("[ERROR] Unknown input file format '%s'!" % args.inputFormat)
        sys.exit(1)

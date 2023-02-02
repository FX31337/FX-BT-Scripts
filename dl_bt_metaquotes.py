#!/usr/bin/env python
# -*- coding: utf-8 -*-

import argparse
import urllib.request
from urllib.error import URLError
import re
from datetime import date
import os
import sys
from struct import unpack, unpack_from, calcsize
from itertools import cycle
import lzo
import hashlib
import binascii
import datetime
import csv

userAgent = "Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0)"


def error(message, exit=True):
    print("[ERROR] ", message)
    if exit:
        sys.exit(1)


def fetchHistoryList(pair):
    listUrlTemplate = "http://history.metaquotes.net/symbols/%s/list.txt"
    listUrl = listUrlTemplate % pair
    if args.verbose:
        print("Downloading %s list file from %s ..." % (pair, listUrl))

    history = []
    try:
        request = urllib.request.Request(listUrl, None, {"User-Agent": userAgent})
        with urllib.request.urlopen(request) as response:
            for line in response:
                history += [line.decode("utf-8").rstrip("\n")]
    except URLError as e:
        if hasattr(e, "reason"):
            error(e.reason)
        elif hasattr(e, "code"):
            error(e.code)

    return history


def findHistoryFile(history, pair, year, month):
    for datFile in history:
        if re.match("%s_%s_%02d" % (pair, year, int(month)), datFile):
            return datFile

    return False


def downloadHistoryFile(pair, year, month, historyFile, destination):
    historyPath = os.path.join(
        destination, pair, str(year), "%02d" % int(month), historyFile
    )
    if os.path.isfile(historyPath):
        if args.verbose:
            print("Skipping, file already exists.")
        return

    historyUrlTemplate = "http://history.metaquotes.net/symbols/%s/%s"
    historyUrl = historyUrlTemplate % (pair, historyFile)
    if args.verbose:
        print("Downloading history file from %s to %s ..." % (historyUrl, destination))
    try:
        request = urllib.request.Request(historyUrl, None, {"User-Agent": userAgent})
        os.makedirs(os.path.dirname(historyPath), mode=0o755, exist_ok=True)
        with urllib.request.urlopen(request) as response, open(historyPath, "wb") as h:
            h.write(response.read())
    except URLError as e:
        if hasattr(e, "reason"):
            error(e.reason)
        elif hasattr(e, "code"):
            error(e.code)
    except OSError as e:
        error(e.strerror)


ENDIAN = "little"
TAIL = b"\x11\x00\x00"  # For checking: Packed buffer is alway contains the 3 last bytes = {0x11, 0, 0}
PRECISION = 140


def big_int(arr):
    """make an array of ints (4 bytes) into one big int
    arr[0] holds the LSB in its MSB position
    ie. the layout of bytes in memory is reversed from what it represents"""
    # concatenate the bytes of the ints
    bs = b"".join(i.to_bytes(4, ENDIAN) for i in arr)
    return int.from_bytes(bs, ENDIAN)


# could replace with this a single number or some other encoding
#               |LSB
MOD = big_int(
    [
        0x2300905D,
        0x1B6C06DF,
        0xE4D0D140,
        0xED8B47C4,
        0x93970C42,
        0x920C45E6,
        0x22C90AFB,
        0x37B67A10,
        0x0F67F0F6,
        0x4237AB4F,
        0x9FA30B14,
        0x916B3CA6,
        0xD48FA715,
        0x689FCCA6,
        0xD3DBE628,
        0x5200D9B3,
        0x732F7BBC,
        0xDC592279,
        0x39861B5F,
        0x0A007CBA,
        0xBF311219,
        0xD3461CB2,
        0x519A4042,
        0xDE59FBB0,
        0xDD6662ED,
        0xE9D7BAFC,
        0x878F5459,
        0x63294CBF,
        0x103206C9,
        0xD2FA9C90,
        0x49832FEF,
        0xADEAAD39,
        0x00000000,
        0x00000000,
    ]
)
#                                 MSB|
EXP = 17


def decode_key(key, e=EXP, m=MOD):
    """compute key ^ e % m and return the least significant 128 bytes"""
    key = int.from_bytes(key, ENDIAN)
    n = pow(key, e, m)
    # n could be bigger than 128 bytes, so give it extra room
    bs = n.to_bytes(PRECISION, ENDIAN)
    # we only care about the first 128
    return bs[:128]


def xor_data(key, data):
    """xor each byte of data with that of key, cycling over key as needed"""
    return bytes(d ^ k for d, k in zip(data, cycle(key)))


def decode_body(buf, decompress=True):
    """given the bytes from a .dat file, decode it"""
    head = buf[:0x88]
    key = decode_key(buf[0x88 : 0x88 + 0x80])
    body = xor_data(key, buf[0x108:])
    expected_pack_size = len(buf) - 0x110
    packed_size, unpacked_size = unpack_from("<L I", body)
    if expected_pack_size != packed_size:
        raise Exception("Wrong packed size")
    if body[-3:] != TAIL:
        raise Exception("Trailing 3 bytes not correct")
        pass
    # this is needed to play nice with the lzo api
    if decompress:
        magic = b"\xf0" + unpacked_size.to_bytes(4, "big")
        data = lzo.decompress(magic + body[8:])
        return head, data
    else:
        return head, body


# MetaQuotes Format Decompressor
#
# A .dat file contains 3 main types of blocks: Type-1, Type-2 and Type-3.
# Every data file starts with Type-1 block(s) since this type stores exact
# values for timestamp, open/high/low/close prices and the volume. After a
# Type-1 block it can be continued with incremental types (Type-2 or Type-3).
# Each Type-3 block represents a minute data with incremental open/high/low/close
# price and volume data. Type-2 blocks contain highly compressable minute data
# which have the same values or have just a small difference between eachother,
# but it would need further investigation.
#
def decompress(data, year, month):
    i = 0
    bars = []
    while i < len(data):
        # Type-3 Block
        #   Description : one minute step data, stores only incremental values
        #   Block length: 1 byte flag + streak*5 bytes of data
        #   Flag codes  : 0xca..0xff stores the length of streak in this type of block
        #   Field_1     : 1 byte, open price incremental stored as a signed char and added to previous close price
        #   Field_2     : 1 byte, high price incremental stored as an unsigned char and added to open price
        #   Field_3     : 1 byte, low price incremental stored as an unsigned char and subtracted from open price
        #   Field_4     : 1 byte, close price incremental stored as a signed char and added to open price
        #   Field_5     : 1 byte, volume incremental stored as a signed char

        if data[i] > 0xBF: #191 as decimal
            streak = (
                data[i] - 0xBF
            )  # Get the number of streaks hiding inside this block
            i += 1  # Move index to first data byte of current streak

            # Transform streak bytes into usable data and collect them in 'bars' list
            for s in range(0, streak):
                timestamp = lastBar["timestamp"] + datetime.timedelta(minutes=1)
                open      = lastBar["close"] + unpack("b", bytes([data[i]]))[0]
                high      = open + unpack("B", bytes([data[i + 1]]))[0]
                low       = open - unpack("B", bytes([data[i + 2]]))[0]
                close     = open + unpack("b", bytes([data[i + 3]]))[0]
                volume    = unpack("B", bytes([data[i + 4]]))[0]

                lastBar = {
                    "timestamp": timestamp,
                    "open": open,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "type": 3,
                    "address": i,
                }
                bars += [lastBar]

                # Move index to first byte of next block or type
                i += 5

        # Type-2 Block
        #   Description : kind of repeater type for highly compressable one minute step data
        #   Block length: 1 byte flag + streak*6 bytes of data
        #   Flag codes  : 0x8a..0xbf stores the length of streak in this type of block
        #   Field_1     : timestamp incremental to previous timestamp
        #   Field_2     : 1 byte, open price incremental stored as a signed char and added to previous close price
        #   Field_3     : 1 byte, high price incremental stored as an unsigned char and added to open price
        #   Field_4     : 4 bytes, low price incremental stored as an unsigned short subtracted from open price
        #   Field_5     : 4 bytes, close price incremental stored as an unsigned short and added to open price
        #   Field_6     : 1 byte, volume incremental stored as a signed char
        elif data[i] > 0x7F:
            streak = (
                data[i] - 0x7F
            )  # Get the number of streaks hiding inside this block
            i += 1  # Move index to first data byte of current streak            

            timestamp = lastBar["timestamp"] + datetime.timedelta(minutes=1)

            open      = lastBar["close"] + unpack("b", bytes([data[i]]))[0]
            high      = open + unpack("B", bytes([data[i + 1]]))[0]
            low       = open - unpack("<H", data[i + 8  : i + 10])[0]
            close     = open + unpack("<H", data[i + 10  : i + 12])[0]
            volume    = unpack("B", bytes([data[i + 9]]))[0]

            lastBar = {
                "timestamp": timestamp,
                "open"     : open,
                "high"     : high,
                "low"      : low,
                "close"    : close,
                "volume"   : volume,
                "type"     : 2,
                "address"  : i,
            }

            bars += [
                lastBar
            ]  # *WARNING* It adds just one bar for now but the block can contain much more bars!

            # Move index to first byte of next block or type
            i += streak * 6

        # Type-1 Block
        #   Description : kind of synchronization type, stores exact values
        #   Block length: 1 byte flag + streak*16 bytes of data
        #   Flag codes  : 0x4a..0x7f stores the length of streak in this type of block
        #   Byte order  : Little-Endian
        #   Field_1     : 4 bytes, timestamp stored as an unsigned integer
        #   Field_2     : 4 bytes, open price stored as an unsigned integer and multiplied by 100,000
        #   Field_3     : 4 bytes, high price stored as a unsigned short added to open price
        #   Field_4     : 4 bytes, low price stored as a unsigned short added to open price
        #   Field_5     : 4 bytes, close price stored as a signed short added to open price
        #   Field_6     : 4 bytes, volume stored as a unsigned short
        elif data[i] > 0x3F:
            streak = (
                data[i] - 0x3F
            )  # Get the number of streaks hiding inside this block
            i += 1  # Move index to first data byte of current streak

            # Transform streak bytes into usable data and collect them in 'bars' list
            for s in range(0, streak):
                timestamp = datetime.datetime.fromtimestamp(
                    unpack("<I", data[i : i + 4])[0], datetime.timezone.utc
                )
                open   = unpack("<I", data[i + 4 : i + 8])[0]
                high   = open + unpack("<H", data[i + 8  : i + 10])[0]
                low    = open - unpack("<H", data[i + 10 : i + 12])[0]
                close  = open + unpack("<h", data[i + 12 : i + 14])[0]
                volume = unpack("<H", data[i + 14 : i + 16])[0]

                lastBar = {
                    "timestamp": timestamp,
                    "open": open,
                    "high": high,
                    "low": low,
                    "close": close,
                    "volume": volume,
                    "type": 1,
                    "address": i,
                }
                bars += [lastBar]

                # Move index to first byte of next block or type
                i += 16
        else:
            i += 1
    return bars


def anomalyTest(bars):
    for bar in bars:
        anomalies = []
        if bar["open"] > bar["high"] or bar["open"] < bar["low"]:
            anomalies += ["open"]
        if max([bar["open"], bar["high"], bar["low"], bar["close"]]) != bar["high"]:
            anomalies += ["high"]
        if min([bar["open"], bar["high"], bar["low"], bar["close"]]) != bar["low"]:
            anomalies += ["low"]
        if bar["close"] > bar["high"] or bar["close"] < bar["low"]:
            anomalies += ["close"]

        if len(anomalies):
            print(
                "[ANOMALY] %s  Type-%d  %s"
                % (
                    bar["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                    bar["type"],
                    hex(bar["address"]),
                ),
                end="   ",
            )
            for anomaly in anomalies:
                print("%s" % anomaly, end=" ")
            print()


def convertToCsv(pair, year, month, historyFile, destination):
    # return a string of the md5 checksum for the bytes `b`
    digest = lambda b: binascii.hexlify(hashlib.md5(b).digest()).decode()

    if args.verbose:
        print("Converting to CSV ...")

    historyPath = os.path.join(
        destination, 
        pair, 
        str(year), 
        "%02d" % int(month), 
        historyFile
    )

    csvPath = os.path.join(
        destination,
        pair,
        str(year),
        "%02d" % int(month),
        "%s-%02d.csv" % (str(year), int(month)),
    )

    with open(historyPath, "rb") as datInput, open(csvPath, "wt") as csvOutput:
        buf = datInput.read()
        matches = re.search(r"([a-z0-9]+)\.dat", historyFile).groups()

        if len(matches) != 1 or len(matches[0]) != 32:
            raise Exception("Error with MD5 from filename")

        md5 = matches[0]

        if digest(buf) != md5:
            raise Exception("Checksum does not match")

        head, data = decode_body(buf)
        bars = decompress(data, year, month)

        if args.anomaly:
            anomalyTest(bars)

        csvWriter = csv.writer(
            csvOutput, 
            delimiter=",", 
            quotechar='"', 
            quoting=csv.QUOTE_MINIMAL
        )

        # Build timedelta object from time offset
        timeOffsetMatch = re.match(
            r"(?P<sign>[+-]?)(?P<hours>\d{2})(?P<minutes>\d{2})", args.timeOffset
        )
        if timeOffsetMatch:
            timeOffsetGroup = timeOffsetMatch.groupdict()

            timeOffset = datetime.timedelta(
                hours=int(timeOffsetGroup["sign"] + timeOffsetGroup["hours"]),
                minutes=int(timeOffsetGroup["sign"] + timeOffsetGroup["minutes"]),
            )
        else:
            timeOffset = datetime.timedelta(0)

        for bar in bars:
            csvWriter.writerow(
                [
                    (bar["timestamp"] + timeOffset).strftime("%Y-%m-%d %H:%M:%S"),
                    bar["open"] / 1e5,
                    bar["high"] / 1e5,
                    bar["low"] / 1e5,
                    bar["close"] / 1e5,
                    bar["volume"],
                ]
            )


if __name__ == "__main__":
    # Parse arguments
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument(
        "-p",
        "--pairs",
        action="store",
        dest="pairs",
        help="Pair(s) to download (separated by comma).",
        default="all",
    )
    argumentParser.add_argument(
        "-y",
        "--years",
        action="store",
        dest="years",
        help="Year(s) to download (separated by comma).",
        default="all",
    )
    argumentParser.add_argument(
        "-m",
        "--months",
        action="store",
        dest="months",
        help="Month(s) to download (separated by comma).",
        default="all",
    )
    argumentParser.add_argument(
        "-d",
        "--destination",
        action="store",
        dest="destination",
        help="Directory to download files.",
        default="download/metaquotes",
    )
    argumentParser.add_argument(
        "-c",
        "--csv-convert",
        action="store_true",
        dest="convert",
        help="Perform CSV conversion.",
    )
    argumentParser.add_argument(
        "-t",
        "--time-offset",
        action="store",
        dest="timeOffset",
        help="Time offset for timestamps in +/-HHMM format.",
        default="",
    )
    argumentParser.add_argument(
        "-a",
        "--anomaly-test",
        action="store_true",
        dest="anomaly",
        help="Run anomaly tests during conversion.",
    )
    argumentParser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        dest="verbose",
        help="Increase output verbosity.",
    )
    args = argumentParser.parse_args()

    allPairs = [
        "AUDJPY",
        "AUDNZD",
        "AUDUSD",
        "CADJPY",
        "CHFJPY",
        "EURAUD",
        "EURCAD",
        "EURCHF",
        "EURGBP",
        "EURJPY",
        "EURNOK",
        "EURSEK",
        "EURUSD",
        "GBPCHF",
        "GBPJPY",
        "GBPUSD",
        "NZDUSD",
        "USDCAD",
        "USDCHF",
        "USDJPY",
        "USDNOK",
        "USDSEK",
        "USDSGD",
        "AUDCAD",
        "AUDCHF",
        "CADCHF",
        "EURNZD",
        "GBPAUD",
        "GBPCAD",
        "GBPNZD",
        "NZDCAD",
        "NZDCHF",
        "NZDJPY",
        "XAGUSD",
        "XAUUSD",
    ]

    pairs = allPairs if args.pairs == "all" else args.pairs.split(",")
    years = (
        range(1970, date.today().year + 1)
        if args.years == "all"
        else args.years.split(",")
    )
    months = range(1, 12 + 1) if args.months == "all" else args.months.split(",")

    # Build destination directory structure
    for pair in pairs:
        history = fetchHistoryList(pair)
        for year in years:
            for month in months:
                historyFile = findHistoryFile(history, pair, year, month)
                if historyFile:
                    downloadHistoryFile(
                        pair, year, month, historyFile, args.destination
                    )
                    if args.convert:
                        convertToCsv(pair, year, month, historyFile, args.destination)

# python3 dl_bt_metaquotes.py -p XAUUSD -y 2022 -m 10,11 -c -t YYYY-MM-DD -a -v
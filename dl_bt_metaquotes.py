#!/usr/bin/env python

import argparse
import urllib.request
from urllib.error import  URLError
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

userAgent = 'Mozilla/5.0 (X11; Linux x86_64; rv:42.0) Gecko/20100101 Firefox/42.0)'


def error(message, exit=True):
    print('[ERROR] ', message)
    if exit: sys.exit(1)


def fetchHistoryList(pair):
    listUrlTemplate = 'http://history.metaquotes.net/symbols/%s/list.txt'
    listUrl = listUrlTemplate % pair
    if args.verbose: print('Downloading %s list file from %s ...' % (pair, listUrl))

    history = []
    try:
        request = urllib.request.Request(listUrl, None, {'User-Agent': userAgent})
        with urllib.request.urlopen(request) as response:
            for line in response:
                history += [line.decode('utf-8').rstrip('\n')]
    except URLError as e:
        if hasattr(e, 'reason'):
            error(e.reason)
        elif hasattr(e, 'code'):
            error(e.code)

    return history


def findHistoryFile(history, pair, year, month):
    for datFile in history:
        if re.match('%s_%s_%02d' % (pair, year, int(month)), datFile): return datFile

    return False


def downloadHistoryFile(pair, year, month, historyFile, destination):
    historyPath = os.path.join(destination, pair, str(year), '%02d' % int(month), historyFile)
    if os.path.isfile(historyPath):
        if args.verbose: print('Skipping, file already exists.')
        return

    historyUrlTemplate = 'http://history.metaquotes.net/symbols/%s/%s'
    historyUrl = historyUrlTemplate % (pair, historyFile)
    if args.verbose: print('Downloading history file from %s to %s ...' % (historyUrl, destination))
    try:
        request = urllib.request.Request(historyUrl, None, {'User-Agent': userAgent})
        os.makedirs(os.path.dirname(historyPath), mode=0o755, exist_ok=True)
        with urllib.request.urlopen(request) as response, open(historyPath, 'wb') as h:
            h.write(response.read())
    except URLError as e:
        if hasattr(e, 'reason'):
            error(e.reason)
        elif hasattr(e, 'code'):
            error(e.code)
    except OSError as e:
        error(e.strerror)


ENDIAN = 'little'
TAIL = b'\x11\x00\x00'  # For checking: Packed buffer is alway contains the 3 last bytes = {0x11, 0, 0}
PRECISION = 140

def big_int(arr):
    """make an array of ints (4 bytes) into one big int
    arr[0] holds the LSB in its MSB position
    ie. the layout of bytes in memory is reversed from what it represents"""
    # concatenate the bytes of the ints
    bs = b''.join(i.to_bytes(4, ENDIAN) for i in arr)
    return int.from_bytes(bs, ENDIAN)


# could replace with this a single number or some other encoding
#               |LSB
MOD = big_int([0x2300905D, 0x1B6C06DF, 0xE4D0D140, 0xED8B47C4,
               0x93970C42, 0x920C45E6, 0x22C90AFB, 0x37B67A10,
               0x0F67F0F6, 0x4237AB4F, 0x9FA30B14, 0x916B3CA6,
               0xD48FA715, 0x689FCCA6, 0xD3DBE628, 0x5200D9B3,
               0x732F7BBC, 0xDC592279, 0x39861B5F, 0x0A007CBA,
               0xBF311219, 0xD3461CB2, 0x519A4042, 0xDE59FBB0,
               0xDD6662ED, 0xE9D7BAFC, 0x878F5459, 0x63294CBF,
               0x103206C9, 0xD2FA9C90, 0x49832FEF, 0xADEAAD39,
               0x00000000, 0x00000000])
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
    key = decode_key(buf[0x88:0x88 + 0x80])
    body = xor_data(key, buf[0x108:])
    expected_pack_size = len(buf) - 0x110
    packed_size, unpacked_size = unpack_from('<L I', body)
    if expected_pack_size != packed_size:
        raise Exception('Wrong packed size')
    if body[-3:] != TAIL:
        raise Exception('Trailing 3 bytes not correct')
        pass
    # this is needed to play nice with the lzo api
    if decompress:
      magic = b'\xf0' + unpacked_size.to_bytes(4, 'big')
      data = lzo.decompress(magic + body[8:])
      return head, data
    else:
      return head, body


def decompress(data, year, month):
    startDate = datetime.datetime(int(year), int(month)    , 1, 0, 0, tzinfo=datetime.timezone.utc)
    endDate   = datetime.datetime(int(year), int(month) + 1, 1, 0, 0, tzinfo=datetime.timezone.utc)
    i = 0
    bars = []
    while i < len(data) - 16:
        timestamp = datetime.datetime.fromtimestamp(unpack('<i', data[i + 1:i + 1 + 4])[0], datetime.timezone.utc)  # This won't be needed anymore when the full structure will be got revealed
        # Type3 test
        if data[i] > 0xbf:
            streak = data[i] - 0xbf
            i += 1
            for s in range(0, streak):
                timestamp = lastBar['timestamp'] + datetime.timedelta(minutes=1)
                open      = lastBar['close'] + unpack('b', bytes([data[i    ]]))[0]
                high      =            open  + unpack('b', bytes([data[i + 1]]))[0]
                low       =            open  - unpack('b', bytes([data[i + 2]]))[0]
                close     =            open  + unpack('b', bytes([data[i + 3]]))[0]
                volume    =                    unpack('b', bytes([data[i + 4]]))[0]
                lastBar = {
                    'timestamp': timestamp,
                         'open': open,
                         'high': high,
                          'low': low,
                        'close': close,
                       'volume': volume
                }
                bars += [lastBar]
                i += 5
        # Type2 test
        elif data[i] > 0x7f:
            i += 1
        # Type1 test
        elif data[i] > 0x3f:
            # Check if it's a real Type1 bar or not
            if timestamp < startDate or timestamp >= endDate:
                i += 1
                continue
            # Yes, it's really Type1
            streak = data[i] - 0x3f
            i += 1
            for s in range(0, streak):
                timestamp = datetime.datetime.fromtimestamp(
                                   unpack('<i', data[i     :i +  4])[0], datetime.timezone.utc)
                open      =        unpack('<i', data[i +  4:i +  8])[0]
                high      = open + unpack('<h', data[i +  8:i + 10])[0]
                low       = open - unpack('<h', data[i + 10:i + 12])[0]
                close     = open + unpack('<h', data[i + 12:i + 14])[0]
                volume    =        unpack('<H', data[i + 14:i + 16])[0]
                lastBar = {
                    'timestamp': timestamp,
                         'open': open,
                         'high': high,
                          'low': low,
                        'close': close,
                       'volume': volume
                }
                bars += [lastBar]
                i += 16
        else:
            i += 1
    return bars


def convertToCsv(pair, year, month, historyFile, destination):
    # return a string of the md5 checksum for the bytes `b`
    digest = lambda b: binascii.hexlify(hashlib.md5 (b).digest()).decode()

    if args.verbose: print('Converting to CSV ...')
    historyPath = os.path.join(destination, pair, str(year), '%02d' % int(month), historyFile)
    csvPath = os.path.join(destination, pair, str(year), '%02d' % int(month), '%s-%02d.csv' % (str(year), int(month)))
    with open(historyPath, 'rb') as datInput, open(csvPath, 'wt') as csvOutput:
        buf = datInput.read()
        matches = re.search(r'([a-z0-9]+)\.dat', historyFile).groups()
        if len(matches) != 1 or len(matches[0]) != 32:
            raise Exception('Error with MD5 from filename')
        md5 = matches[0]
        if digest(buf) != md5:
            raise Exception('Checksum does not match')
        head, data = decode_body(buf)
        bars = decompress(data, year, month)
        csvWriter = csv.writer(csvOutput, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        # Build timedelta object from time offset
        timeOffsetMatch = re.match(r'(?P<sign>[+-]?)(?P<hours>\d{2})(?P<minutes>\d{2})', args.timeOffset)
        if timeOffsetMatch:
            timeOffsetGroup = timeOffsetMatch.groupdict()
            timeOffset = datetime.timedelta(  hours=int(timeOffsetGroup['sign'] + timeOffsetGroup['hours'  ]),
                                            minutes=int(timeOffsetGroup['sign'] + timeOffsetGroup['minutes']))
        else:
            timeOffset = datetime.timedelta(0)

        for bar in bars:
            csvWriter.writerow([
                (bar['timestamp'] + timeOffset).strftime('%Y-%m-%d %H:%M:%S'),
                bar['open']/1e5,
                bar['high']/1e5,
                bar['low']/1e5,
                bar['close']/1e5,
                bar['volume']
            ])


if __name__ == '__main__':
    # Parse arguments
    argumentParser = argparse.ArgumentParser()
    argumentParser.add_argument('-p', '--pairs',       action='store',      dest='pairs',       help='Pair(s) to download (separated by comma).', default='all')
    argumentParser.add_argument('-y', '--years',       action='store',      dest='years',       help='Year(s) to download (separated by comma).', default='all')
    argumentParser.add_argument('-m', '--months',      action='store',      dest='months',      help='Month(s) to download (separated by comma).', default='all')
    argumentParser.add_argument('-d', '--destination', action='store',      dest='destination', help='Directory to download files.', default='download/metaquotes')
    argumentParser.add_argument('-c', '--csv-convert', action='store_true', dest='convert',     help='Perform CSV conversion.')
    argumentParser.add_argument('-t', '--time-offset', action='store',      dest='timeOffset',  help='Time offset for timestamps in +/-HHMM format.', default='')
    argumentParser.add_argument('-v', '--verbose',     action='store_true', dest='verbose',     help='Increase output verbosity.')
    args = argumentParser.parse_args()

    allPairs = ['AUDJPY', 'AUDNZD', 'AUDUSD', 'CADJPY', 'CHFJPY', 'EURAUD', 'EURCAD',
                'EURCHF', 'EURGBP', 'EURJPY', 'EURNOK', 'EURSEK', 'EURUSD', 'GBPCHF',
                'GBPJPY', 'GBPUSD', 'NZDUSD', 'USDCAD', 'USDCHF', 'USDJPY', 'USDNOK',
                'USDSEK', 'USDSGD', 'AUDCAD', 'AUDCHF', 'CADCHF', 'EURNZD', 'GBPAUD',
                'GBPCAD', 'GBPNZD', 'NZDCAD', 'NZDCHF', 'NZDJPY', 'XAGUSD', 'XAUUSD' ]

    pairs  = allPairs if args.pairs  == 'all' else args.pairs.split(',')
    years  = range(1970, date.today().year + 1) if args.years  == 'all' else args.years.split(',')
    months = range(1, 12 + 1) if args.months == 'all' else args.months.split(',')

    # Build destination directory structure
    for pair in pairs:
        history = fetchHistoryList(pair)
        for year in years:
            for month in months:
                historyFile = findHistoryFile(history, pair, year, month)
                if historyFile:
                    downloadHistoryFile(pair, year, month, historyFile, args.destination)
                    if args.convert:
                        convertToCsv(pair, year, month, historyFile, args.destination)

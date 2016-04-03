#!/usr/bin/env python3
import struct
import datetime
import argparse
import sys

def get_fields_size(spec):
    fmt_str = ''.join(x[1] for x in spec)
    return struct.calcsize(fmt_str)

class BStruct():
    def __init__(self, buf, offset = 0):
        for (name, fmt, *rest) in self._fields:
            field_size = struct.calcsize(fmt)
            val = struct.unpack_from(self._endianness + fmt, buf, offset)

            # Flatten the single-element arrays
            if type(val) is tuple and len(val) == 1:
                val = val[0]

            setattr(self, name, val)

            offset += field_size

    def __str__(self):
        ret = ''

        for (name, _, *fmt) in self._fields:
            val_repr = getattr(self, name)

            # Pretty print the value using the custom formatter.
            if len(fmt):
                pp ,= fmt
                val_repr = pp(self, getattr(self, name))

            ret += '{} = {}\n'.format(name, val_repr)

        return ret

#
# Pretty printers
#
def pretty_print_time(obj, x):
    return datetime.datetime.fromtimestamp(x)

def pretty_print_string(obj, x):
    return x.decode('utf-8').rstrip('\0')

def pretty_print_ignore(obj, x):
    return '<...>'

def pretty_print_hex(obj, x):
    return '{:08x}'.format(x)

def pretty_print_compact(obj, x):
    if any(x): return x
    return '[\\x00] * {}'.format(len(x))

#
# Structure definitions
#
class TicksRaw(BStruct):
    _endianness = '<'
    _fields = [
            ('symbol', '12s', pretty_print_string),
            ('time', 'I', pretty_print_time),
            ('bid', 'd'),
            ('ask', 'd'),
            ('counter', 'I'),
            ('unknown', 'I'),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 40)

class SymbolSel(BStruct):
    _endianness = '<'
    _fields = [
            ('symbol', '12s', pretty_print_string),
            ('digits', 'I'),
            ('index', 'I'),
            ('unknown_1', 'I'),
            ('group', 'I'),
            ('unknown_2', 'I'),
            ('pointSize', 'd'),
            ('spread', 'I'),
            ('unknown_3', 'I'),
            ('tickType', 'I'),
            ('unknown_4', 'H'),
            ('unknown_5', 'H'),
            ('time', 'I', pretty_print_time),
            ('unknown_6', 'I'),
            ('bid', 'd'),
            ('ask', 'd'),
            ('sessionHigh', 'd'),
            ('sessionLow', 'd'),
            ('unknown_17', '16s', pretty_print_compact),
            ('bid_2', 'd'),
            ('ask_2', 'd')
            ]
    _size = get_fields_size(_fields)
    assert(_size == 128)

class Symgroups(BStruct):
    _endianness = '<'
    _fields = [
            ('name', '16s', pretty_print_string),
            ('description', '60s', pretty_print_string),
            ('backgroundColor', 'I')
            ]
    _size = get_fields_size(_fields)
    assert(_size == 80)

class SymbolsRaw(BStruct):
    _endianness = '<'
    _fields = [
            ('name', '12s', pretty_print_string),
            ('description', '64s', pretty_print_string),
            ('altName', '12s', pretty_print_string),
            ('baseCurrency', '12s', pretty_print_string),
            ('group', 'I'),
            ('digits', 'I'),
            ('tradeMode', 'I'),
            ('backgroundColor', 'I', pretty_print_hex),
            ('id', 'I'),
            ('unknown_1', '1508c', pretty_print_ignore),
            ('unknown_2', 'I'),
            ('unknown_3', '8c'),
            ('unknown_4', 'd'),
            ('unknown_5', '12s', pretty_print_compact),
            ('spread', 'I'),
            ('unknown_6', '16s', pretty_print_compact),
            ('swapLong', 'd'),
            ('swapShort', 'd'),
            ('unknown_7', 'I'),
            ('unknown_8', 'I'),
            ('contractSize', 'd'),
            ('unknown_9', '16s', pretty_print_compact),
            ('stopDistance', 'I'),
            ('unknown_10', '12s', pretty_print_compact),
            ('marginInit', 'd'),
            ('marginMaintenance', 'd'),
            ('marginHedged', 'd'),
            ('marginDivider', 'd'),
            ('pointSize', 'd'),
            ('pointsPerUnit', 'd'),
            ('unknown_11', '24s', pretty_print_compact),
            ('marginCurrency', '12s', pretty_print_string),
            ('unknown_12', '104s', pretty_print_ignore),
            ('unknown_13', 'I'),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 1936)

class FxtHeader(BStruct):
    _endianness = '<'
    _fields = [
            # Build header
            ('headerVersion', 'I'),
            ('copyright', '64s', pretty_print_string),
            ('server', '128s', pretty_print_string),
            ('symbol', '12s', pretty_print_string),
            ('timeframe', 'i'),
            ('modelType', 'i'),
            ('totalBars', 'I'),
            ('modelStart', 'I', pretty_print_time),
            ('modelEnd', 'I', pretty_print_time),
            ('padding1', '4s', pretty_print_ignore),

            # General parameters
            ('modelQuality', 'd'),
            ('baseCurrency', '12s', pretty_print_string),
            ('spread', 'I'),
            ('digits', 'I'),
            ('padding2', '4s', pretty_print_ignore),
            ('pointSize', 'd'),
            ('minLotSize', 'i'),
            ('maxLotSize', 'i'),
            ('lotStep', 'i'),
            ('stopLevel', 'i'),
            ('GTC', 'i'),
            ('padding3', '4s', pretty_print_ignore),

            # Profit Calculation parameters
            ('contractSize', 'd'),
            ('tickValue', 'd'),
            ('tickSize', 'd'),
            ('profitMode', 'i'),
            ('swapEnabled', 'i'),
            ('swapMethod', 'i'),
            ('padding4', '4s', pretty_print_ignore),
            ('swapLong', 'd'),
            ('swapShort', 'd'),
            ('swapRollover', 'i'),

            # Margin calculation
            ('accountLeverage', 'i'), # Default: 100
            ('freeMarginMode', 'i'),
            ('marginCalcMode', 'i'),
            ('marginStopoutLevel', 'i'),
            ('marginStopoutMode', 'i'),
            ('marginRequirements', 'd'),
            ('marginMaintenanceReq', 'd'),
            ('marginHedgedPosReq', 'd'),
            ('marginLeverageDivider', 'd'),
            ('marginCurrency', '12s', pretty_print_string),
            ('padding5', '4s', pretty_print_ignore),

            # Commission calculation
            ('commission', 'd'),
            ('commissionType', 'i'),
            ('commissionPerEntry', 'i'),

            # For internal use
            ('indexOfFirstBar', 'i'),
            ('indexOfLastBar', 'i'),
            ('indexOfM1Bar', 'i'),
            ('indexOfM5Bar', 'i'),
            ('indexOfM15Bar', 'i'),
            ('indexOfM30Bar', 'i'),
            ('indexOfH1Bar', 'i'),
            ('indexOfH4Bar', 'i'),
            ('beginDate', 'I', pretty_print_time),
            ('endDate', 'I', pretty_print_time),
            ('freezeLevel', 'i'),
            ('numberOfErrors', 'I'),
            ('reserved', '240s', pretty_print_ignore),
            ]
    _size = get_fields_size(_fields)
    assert(_size == 728)

def dump_content(filename, offset, strucc):
    """
    Dump the content of the file "filename" starting from offset and using the
    BStruct subclass pointed by strucc
    """
    try:
        fp = open(filename, 'rb')
    except OSError as e:
            print("[ERROR] '%s' raised when tried to read the file '%s'" % (e.strerror, filename))
            sys.exit(1)

    fp.seek(offset)

    while True:
        buf = fp.read(strucc._size)

        if len(buf) != strucc._size:
            break

        obj = strucc(buf)
        print(obj)

if __name__ == '__main__':
    # Parse the arguments
    argumentParser = argparse.ArgumentParser(add_help=False)
    argumentParser.add_argument('-i', '--input-file', action='store', dest='inputFile', help='input file', required=True)
    argumentParser.add_argument('-t', '--input-type', action='store', dest='inputType', help='input type', required=True)
    argumentParser.add_argument('-h', '--help', action='help', help='Show this help message and exit')
    args = argumentParser.parse_args()

    if args.inputType == 'sel':
        # There's a 4-byte magic preceding the data
        dump_content(args.inputFile, 4, SymbolSel)
    elif args.inputType == 'ticksraw':
        dump_content(args.inputFile, 0, TicksRaw)
    elif args.inputType == 'symbolsraw':
        dump_content(args.inputFile, 0, SymbolsRaw)
    elif args.inputType == 'symgroups':
        dump_content(args.inputFile, 0, Symgroups)
    elif args.inputType == 'fxt-header':
        dump_content(args.inputFile, 0, FxtHeader)
    else:
        print('Invalid type {}!'.format(args.inputType))

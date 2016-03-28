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

            # Pretty print the value using the custom formatter
            if len(fmt):
                pp, = fmt
                val_repr = pp(self, getattr(self, name))

            ret += '{} = {}\n'.format(name, val_repr)

        return ret

def pretty_print_time(obj, x):
    return datetime.datetime.fromtimestamp(x)

def pretty_print_string(obj, x):
    return x.decode('utf-8')

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
            ('unknown_17', '16c'),
            ('bid_2', 'd'),
            ('ask_2', 'd')
            ]
    _size = get_fields_size(_fields)
    assert(_size == 128)
def dump_content(filename):
    try:
        fp = open(filename, 'rb')
    except OSError as e:
            print("[ERROR] '%s' raised when tried to read the file '%s'" % (e.strerror, filename))
            sys.exit(1)

    magic = fp.read(4)

    while True:
        buf = fp.read(SymbolSel._size)

        if len(buf) != SymbolSel._size:
            break

        obj = SymbolSel(buf)
        print(obj)

if __name__ == '__main__':
    # Parse the arguments
    argumentParser = argparse.ArgumentParser(add_help=False)
    argumentParser.add_argument('-i', '--input-file', action='store', dest='inputFile', help='input file', required=True)
    argumentParser.add_argument('-h', '--help', action='help', help='Show this help message and exit')
    args = argumentParser.parse_args()

    dump_content(args.inputFile)

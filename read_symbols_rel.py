import struct
import datetime
import argparse
import sys

record_length = 128

def dump_content(filename):
    try:
        fp = open(filename, 'rb')
    except OSError as e:
            print("[ERROR] '%s' raised when tried to read the file '%s'" % (e.strerror, filename))
            sys.exit(1)

    magic = fp.read(4)

    while True:
        buf = fp.read(record_length)

        if len(buf) != record_length:
            break

        symbol = buf[:12].decode('utf-8')
        fields = struct.unpack('<IIIIIdIIIHHIIdddd4Idd', buf[12:])

        sym_table = [
                'digits',
                'index',
                None,
                'group',
                None,
                'pointSize',
                'spread',
                None,
                ['tickType', lambda x: ['uptick', 'downtick', 'n/a'][x]],
                None,
                None,
                ['time', lambda x: datetime.datetime.fromtimestamp(x)],
                None,
                'bid',
                'ask',
                'sessionHigh',
                'sessionLow',
                None,
                None,
                None,
                None,
                'bid_2',
                'ask_2',
                ]

        out = 'Symbol: {}\n'.format(symbol)

        for (i, obj) in enumerate(fields):
            handler = sym_table[i]

            if handler == None:
                continue

            if type(handler) is list:
                name = handler[0]
                val = handler[1](obj)
            else:
                name = handler
                val = obj

            out += '{}: {}\n'.format(name, val)

        print(out)

if __name__ == '__main__':
    # Parse the arguments
    argumentParser = argparse.ArgumentParser(add_help=False)
    argumentParser.add_argument('-i', '--input-file', action='store', dest='inputFile', help='input file', required=True)
    argumentParser.add_argument('-h', '--help', action='help', help='Show this help message and exit')
    args = argumentParser.parse_args()

    dump_content(args.inputFile)

import struct
import datetime

def get_fields_size(spec):
    # Prepend an endianness mark to prevent calcsize to insert padding bytes
    fmt_str = '=' + ''.join(x[1] for x in spec)
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

def pretty_print_wstring(obj, x):
    return x.decode('utf-16').rstrip('\0')

def pretty_print_ignore(obj, x):
    return '<...>'

def pretty_print_hex(obj, x):
    return '{:08x}'.format(x)

def pretty_print_compact(obj, x):
    if any(x): return x
    return '[\\x00] * {}'.format(len(x))

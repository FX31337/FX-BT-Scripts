#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from struct import unpack_from, calcsize
from itertools import cycle
import lzo

# For checking: Packed buffer is alway contains the 3 last bytes = {0x11, 0, 0}

ENDIAN = 'little'
TAIL = b'\x11\x00\x00'
PRECISION = 140
# FMT = 'i 64s 36s 12s 8s 12s 128s'

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
    #head = unpack_from(FMT, bs)
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

if __name__ == '__main__':
    import argparse
    import re
    import hashlib
    import binascii
    # return a string of the md5 checksum for the bytes `b`
    digest = lambda b: binascii.hexlify(hashlib.md5 (b).digest()).decode()

    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input-file')
    parser.add_argument('-o', '--output-file')
    parser.add_argument('-n', '--no-decompress', default=False, action='store_true')
    args = parser.parse_args()

    # fhi : file handle in
    # fho : file handle out
    with open(args.input_file, 'rb') as fhi,\
         open(args.output_file, 'wb') as fho:
        buf = fhi.read()
        matches = re.search(r'([a-z0-9]+)\.dat', args.input_file).groups()
        if len(matches) != 1 or len(matches[0]) != 32:
            raise Exception('Error with md5 from filename')
        md5 = matches[0]
        if digest(buf) != md5:
            raise Exception('Checksum does not match')
        head, data = decode_body(buf, decompress=not args.no_decompress)
        fho.write(data)

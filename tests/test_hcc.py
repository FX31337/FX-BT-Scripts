import unittest

import sys
sys.path.append('..')

import os
from struct import unpack

import convert_csv_to_mt


class TestHCCSetup(unittest.TestCase):
    def setUp(self):
        self.hcc_file = convert_csv_to_mt.HCC('.hcc', '/tmp', 1, 'EURUSD')
        self.hcc_file.path.close()
        self.hcc_file.path = open(self.hcc_file.fullname, 'rb')

    def TearDown(self):
        self;hcc_file.path.close()
        os.remove(full_name)


class TestHCCParameter(TestHCCSetup):
    def test_arg_option(self):
        args = convert_csv_to_mt.config_argparser().parse_args(['-f', 'hcc', '-i', 'foo'])
        self.assertEqual('hcc', args.outputFormat.lower())


class TestHCCFileName(TestHCCSetup):
    def test_filename_extension(self):
        self.assertEqual('EURUSD1.hcc', self.hcc_file.filename)


class TestHCCFileHeader(TestHCCSetup):
    def setUp(self):
        super().setUp()
        self.hcc_file.path.seek(0)
        self.hcc_header = self.hcc_file.path.read(228)

    def test_file_header_magic_field(self):
        self.assertEqual((501,), unpack('<I', self.hcc_header[:4]))

    def test_file_header_copyright_field(self):
        self.assertEqual(u'Copyright 2001-2016, MetaQuotes Software Corp.',
            self.hcc_header[4:132].decode('utf-16').replace('\x00', ''))

    def test_file_header_name_field(self):
        self.assertEqual(u'History',
            self.hcc_header[134:164].decode('utf-16').replace('\x00', ''))

    def test_header_title_field(self):
        self.assertEqual(u'EURUSD',
            self.hcc_header[168:228].decode('utf-16').replace('\x00', ''))


if __name__ == '__main__':
    unittest.main()

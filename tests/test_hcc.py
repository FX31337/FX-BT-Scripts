import unittest

import sys
sys.path.append('..')

import convert_csv_to_mt

class TestHCCParameter(unittest.TestCase):
    def test_arg_option(self):
        args = convert_csv_to_mt.config_argparser().parse_args(['-f', 'hcc', '-i', 'foo'])
        self.assertEqual('hcc', args.outputFormat.lower())

class TestHCCFileName(unittest.TestCase):
    def test_filename_extension(self):
        self.assertEqual('foo10.hcc', convert_csv_to_mt._hccFilename('foo', 10))

if __name__ == '__main__':
    unittest.main()

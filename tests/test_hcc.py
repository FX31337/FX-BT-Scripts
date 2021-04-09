# -*- coding: utf-8 -*-
import unittest

import sys

sys.path.append("..")

import os
from struct import unpack

import importlib

conv_from_csv = importlib.import_module("fx-data-convert-from-csv")


class TestHCCSetup(unittest.TestCase):
    def setUp(self):
        self.hcc_file = conv_from_csv.HCC(".hcc", "/tmp", 1, "EURUSD")
        self.hcc_file.path.close()
        self.hcc_file.path = open(self.hcc_file.fullname, "rb")

    def TearDown(self):
        self.hcc_file.path.close()
        os.remove(full_name)


class TestHCCParameter(TestHCCSetup):
    def test_arg_option(self):
        args = conv_from_csv.config_argparser().parse_args(["-f", "hcc", "-i", "foo"])
        self.assertEqual("hcc", args.outputFormat.lower())


class TestHCCFileName(TestHCCSetup):
    def test_filename_extension(self):
        self.assertEqual("EURUSD1.hcc", self.hcc_file.filename)


class TestHCCGenerateFile(TestHCCSetup):
    def setUp(self):
        super().setUp()

        self.hcc_file.path.seek(0)

        self.hcc_header = self.hcc_file.path.read(228)
        self.hcc_main_table = self.hcc_file.path.read(18)
        self.hcc_empty_table = self.hcc_file.path.read(18)
        self.hcc_record_header = self.hcc_file.path.read(189)

    def test_file_header_magic_field(self):
        self.assertEqual((501,), unpack("<I", self.hcc_header[:4]))

    def test_file_header_copyright_field(self):
        self.assertEqual(
            u"Copyright 2001-2016, MetaQuotes Software Corp.",
            self.hcc_header[4:132].decode("utf-16").replace("\x00", ""),
        )

    def test_file_header_name_field(self):
        self.assertEqual(
            u"History", self.hcc_header[132:164].decode("utf-16").replace("\x00", "")
        )

    def test_header_title_field(self):
        self.assertEqual(
            u"EURUSD", self.hcc_header[164:228].decode("utf-16").replace("\x00", "")
        )

    def test_table(self):
        self.assertEqual((0,), unpack("<i", self.hcc_main_table[:4]))  # unknow_0
        self.assertEqual((0,), unpack("<i", self.hcc_main_table[4:8]))  # unknow_1
        self.assertEqual((0,), unpack("<h", self.hcc_main_table[8:10]))  # unknow_2
        self.assertEqual((0,), unpack("<i", self.hcc_main_table[10:14]))  # size
        self.assertEqual((0,), unpack("<i", self.hcc_main_table[14:18]))  # offset


if __name__ == "__main__":
    unittest.main()

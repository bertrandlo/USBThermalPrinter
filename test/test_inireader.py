# coding: utf-8
import unittest
from ini_reader import INIReader


class TestINIReader(unittest.TestCase):

    def test_getProjectPath(self):
        ini_reader = INIReader()
        print(ini_reader.getProjectPath())

    def test_get(self):
        ini_reader = INIReader()
        print(ini_reader.get("format", "footer_margin"))

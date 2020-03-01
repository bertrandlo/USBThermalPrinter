# coding: utf-8
import unittest
from io import StringIO, BytesIO
from thermal_printer import ThermalPrint
from PIL import Image, WmfImagePlugin
from ini_reader import INIReader

class WmfHandler:
    def open(self, im):
        ...
    def load(self, im):
        ...
        return im
    def save(self, im, fp, filename):
        ...


class TestPrinter(unittest.TestCase):

    def __init__(self, *awg, **kawg):
        super().__init__(*awg, **kawg)
        settings = INIReader()
        self.printer = ThermalPrint(printerName=settings.get("General", "printer"),
                                    img_maxWidth=int(settings.get("format", "maxwidthpixels")),
                                    line_spacing=int(settings.get("format", "line_spacing")),
                                    header_margin=int(settings.get("format", "header_margin")),
                                    footer_margin=int(settings.get("format", "footer_margin")),
                                    cutting=settings.get("format", "cutting"))

    def testLoad(self):
        with open('gdtest1.jpg', 'rb') as fin:
            bytes = BytesIO(fin.read())

        self.printer.load(bytes)
        self.printer.printing()

    def testPrintDC(self):
        import win32ui
        import win32print
        import win32con

        INCH = 1440

        hDC = win32ui.CreateDC()
        hDC.CreatePrinterDC(win32print.GetDefaultPrinter())
        hDC.StartDoc("Test doc")
        hDC.StartPage()
        hDC.SetMapMode(win32con.MM_TWIPS)
        hDC.DrawText("TEST", (0, INCH * -1, INCH * 8, INCH * -2), win32con.DT_CENTER)
        hDC.EndPage()
        hDC.EndDoc()

    def testPrint(self):
        self.printer.printing(content="愛情可樂糖\n\n\n愛情可樂糖\n\n\n")

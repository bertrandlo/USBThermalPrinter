# coding: utf-8
from distutils.core import setup
import py2exe

setup(
    windows=['receive.py', {"script": "receive.py", "icon_resources": [(1, "printer.ico")]}],
    options={
        'py2exe': {'bundle_files': 3,  # 3 - not bundle to single execute file
                    "packages": ["PIL"],
                    "excludes": ["tcl", "Tkinter", "PySide"],
                    "includes": ["sip", "PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtNetwork", "PyQt5.QtWidgets"],
                    "dll_excludes": ["mswsock.dll", "powrprof.dll", "tcl85.dll", "tk85.dll"]}
    },
    data_files=[('imageformats',      # QT 圖形格式轉換函式庫
                   ['C:\\Users/brt/PycharmProjects/USBThermalPrinter/venv/Lib/site-packages/PyQt5/Qt/plugins/imageformats/qjpeg.dll',
                    'C:\\Users/brt/PycharmProjects/USBThermalPrinter/venv/Lib/site-packages/PyQt5/Qt/plugins/imageformats/qgif.dll',
                    'C:\\Users/brt/PycharmProjects/USBThermalPrinter/venv/Lib/site-packages/PyQt5/Qt/plugins/imageformats/qico.dll',
                    'C:\\Users/brt/PycharmProjects/USBThermalPrinter/venv/Lib/site-packages/PyQt5/Qt/plugins/imageformats/qsvg.dll',
                    'C:\\Users/brt/PycharmProjects/USBThermalPrinter/venv/Lib/site-packages/PyQt5/Qt/plugins/imageformats/qtiff.dll'
                    ],)],
)
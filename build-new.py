# For CX_Freeze  Using "python build-new.py build"
import sys
from cx_Freeze import setup, Executable
# from PyQt5 import QtWebEngine
# Dependencies are automatically detected, but it might need fine tuning.
includes = ["PyQt5"]
base="C:\\\\Users\\brt\\PycharmProjects\\USBThermal\Printer\\venv\\"
build_exe_options = {"packages": ["os"],
                    'includes': includes,
                    'include_files': ["settings.ini", "printer.ico"],
                     "excludes": ["tcl", "Tkinter"],
                     #"zip_include_packages": ["PyQt5"],
                     'bin_excludes': ["Qt5WebEngineCore.dll"]}

# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(  name="receive",
        version="0.1",
        description="Thermal Printer Service",
        options={"build_exe": build_exe_options},
        executables=[Executable("receive.py", base=base, icon="printer.ico")])
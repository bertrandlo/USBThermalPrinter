# coding: utf-8
import logging, sys
from PyQt5.QtCore import QSettings
from PyQt5.Qt import QApplication
import escconv

if __name__ == '__main__':
    settings = QSettings("settings.ini", QSettings.IniFormat)

    guiVisibility = settings.value("guiVisibility", "False")
    printername = settings.value("printer", "GP-5890X") # 預設印表機名稱
    loggingfunc = settings.value("logging", "True")

    settings.setValue("guiVisibility", guiVisibility)
    settings.setValue("printer", printername)
    settings.setValue("logging", loggingfunc)
    settings.sync()

    app = QApplication(sys.argv)
    widget = escconv.UiForm(app)

    if loggingfunc == "True":
        logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.ERROR, format='%(asctime)s - %(levelname)s - %(message)s')

    if guiVisibility == "True":
        widget.show()
    else:
        widget.printer.fnCreateReceivePipe()

    sys.exit(app.exec_())
    sys.exit(0)

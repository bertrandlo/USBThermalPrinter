import os
from pathlib import Path
import configparser


class INIReader:
    def __init__(self):

        config_file_path = Path(self.getProjectPath()).joinpath("settings.ini")
        self.cf = configparser.ConfigParser()
        self.cf.read(config_file_path)

    def getProjectPath(self):
        str = os.path.dirname(os.path.abspath(__file__))
        return str

    def get(self, section, option):
        try:
            ret = self.cf.get(section, option)
            return ret
        except KeyError:
            print("不能獲取到%s選項 %s的值." % (section, option))
            exit(1)

    def set(self, section, option, value):
        return self.cf.set(section, option, value)

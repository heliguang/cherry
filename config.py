from configparser import ConfigParser

configfilename = 'config.ini'

config = ConfigParser()
config.read(configfilename)


class Config(object):

    @classmethod
    def get(cls, section, key):
        return config.get(section, key)


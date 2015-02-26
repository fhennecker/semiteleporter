import ConfigParser
import os, sys
import logging
import shutil
import numpy as np


class Config:
    def __init__(self, configFile=""):
        """ Create a new Config object
        configFile = name of the config file
        """
        self.default = 'default.cfg'
        if(configFile == ""):
            self.configFile = self.default
        else:
            self.configFile = configFile
        self.config = dict()
        self.parser = ConfigParser.ConfigParser()
        self.load()

    def __getitem__(self, index):
        return self.config[index]

    def load(self, configFile=""):
        """ This method read the config file """
        if(configFile != ""):
            self.configFile = configFile

        if(not os.path.exists(self.configFile)):
            if(os.path.exists(self.default)):
                shutil.copy(self.default,self.configFile)
            else:
                logging.error("No '%s' or other config file found" %self.default)
                sys.exit(2)

        logging.info("Loading %s configuration file" % self.configFile)
        self.parser.read(self.configFile)

        for section in self.parser.sections():
            self.config[section] = dict()
            for option in self.parser.options(section):
                value = self.parser.get(section, option)
                try:
                    if(',' in value):
                        self.config[section][option] = np.array(value.split(','), dtype=np.float32)
                    else:
                        self.config[section][option] = float(value)
                except:
                    self.config[section][option] = value

        dest = self.config['File']['save']
        if(dest not in ('', './')):
            if(not os.path.exists(dest)):
                logging.debug("Creating %s directory for pictures" %(dest))
                os.makedirs(dest)
                shutil.copy(self.configFile, os.path.join(dest, self.default))
            self.configFile = os.path.join(dest,self.default)

    def getToStr(self, section, option, toList=True):
        value = self.config
        try:
            value = self.config[section][option]

            if('numpy' in str(type(value))):
                if(toList):
                    value = list(value)
                else:
                    value = str(list(value))[1:-1]
            else:
                value = str(value)
        except:
            logging.error("Bad indexing in Config dico")
        return value
            
    def save(self):
        logging.info("Saving configuration in %s" %(self.configFile))

        for section in self.config:
            for option in self.config[section]:
                value = self.getToStr(section, option,False)
                try:
                    self.parser.set(section, option, value)
                except:
                    self.parser.add_section(section)
                    self.parser.set(section, option, value)
        self.parser.write(open(self.configFile,'w'))
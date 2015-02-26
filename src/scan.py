import sys, os
import logging
import threading
import getopt
import numpy as np
from gui import Gui, Tkinter
from scanner.config import Config
from scanner.camera import Camera, Scene
from scanner.arduino import Arduino, TurnTable, Laser


class Scanner3D(Tkinter.Tk):
    def __init__(self, args):
        """ Create a new Scanner3D object
        args = arguments passed in the command line
        """
        self.config     = Config()
        self.sceneLeft  = None
        self.sceneRight = None
        self.turntable  = None
        self.arduino    = None
        self.gui        = None
        self.directory  = None
        self.logLevel   = logging.WARNING
        self.thread     = threading.Thread(target=self.startScan, args=(False,))
    
        self.parseArgv(args)

    def usage(self, args):
        print("Usage : %s <options>" % args[0])
        print("Available options:")
        print("  --help      , -h             : print this help")
        print("  --config    , -c <filename>  : use filename as configuration file (default=default.cfg)")
        print("  --processing, -p <directory> : use directory as the path to the directory of pictures to process (when you don't use the scanner)")
        print("  --loglevel  , -l <loglevel>  : set logelevel (default=WARNING)")
        print("  --arduino   , -a <path>      : start communication arduino")

    def parseArgv(self,args):
        """ This method parse command line """
        try:
            opts, arguments = getopt.getopt(args[1:],"c:l:p:a:h",["file=", "loglevel=", "directory=", "arduino", "help"])
        except getopt.GetoptError as err:
            logging.error(str(err))
            self.usage(args)
            sys.exit(2)

        for o,a in opts:
            if(o in ("-h", "--help")):
                self.usage(args)
                sys.exit()
            elif(o in ("-c", "--config")):
                self.config = Config(a)
            elif(o in ("-l", "--loglevel")):
                try:
                    self.logLevel = getattr(logging, a.upper())
                    logging.getLogger().setLevel(self.logLevel)
                except:
                    logging.error("Invalid loglevel")
                    sys.exit(2)
            elif(o in ("-p", "--processing")):
                self.directory = a
                self.config = Config(os.path.join(a,'default.cfg'))
            elif(o in ("-a", "--arduino")):
                self.arduino = Arduino(a)
            else:
                assert False, "Unknown option"

    def exportToObjFile(self, filename):
        fp = open(filename, 'w')
        for step in self.sceneRight:
            for point in step:
                fp.write('v %s %s %s\n' %(point.item(0), point.item(1), point.item(2)))
        fp.close()

    def loadConfig(self):
        camera = Camera(self.config['Camera']['port'],
                        (self.config['Camera']['width'], self.config['Camera']['height']),
                        self.config['Camera']['position'],
                        self.config['Camera']['rotation'],
                        self.config['Camera']['viewangle'],
                        (self.config['File']['save'], self.config['File']['extension']),
                        self.directory)

        arduino = Arduino(self.config['Arduino']['port'],
                          True if (self.directory == None) else False)

        self.turntable = TurnTable(self.config['TurnTable']['position'],
                                   self.config['TurnTable']['diameter'],
                                   self.config['TurnTable']['steps'],
                                   arduino)

        # Assume that Laser point to the center of the turntable
        pos = self.config['LaserRight']['position']
        laserRight = Laser(self.config['LaserRight']['pin'],
                           pos,
                           np.arctan(pos[0]/self.turntable.position[2]),
                           arduino)
        self.sceneRight = Scene("right", camera, laserRight, self.turntable)

        pos = self.config['LaserLeft']['position']
        laserLeft = Laser(self.config['LaserLeft']['pin'],
                          pos,
                          np.arctan(pos[0]/self.turntable.position[2]),
                          arduino)
        self.sceneLeft  = Scene("left", camera, laserLeft,  self.turntable)    

    def run(self):
        if(self.arduino != None):
            self.arduino.debugMode()
        else:
            self.gui = Gui(self)
            self.gui.run()

    def startScan(self, startThread=True):
        if(not self.thread.isAlive()):
            self.loadConfig()
            logging.info('\t\033[92m----- Start scanning -----\033[0m')

            logging.info('\033[94m Calibration : free the table and press ENTER...\033[0m')
            if(self.gui == None):
                raw_input('')
            else:
                self.gui.popUpConfirm('Calibration', 'Calibration : free the table and press OK...')
            self.sceneLeft.calibration()
            self.sceneRight.calibration()
            logging.info('\033[94m Calibration : done, place your object on the table and press ENTER...\033[0m')
            if(self.gui == None):
                raw_input('')
            else:
                self.gui.popUpConfirm('Calibration', 'Calibration : Place object and press OK...')

            self.thread = threading.Thread(target=self.startScan, args=(False,))
            self.thread.start()
        elif(not startThread):
            for step in range(self.turntable.nSteps):
                self.sceneLeft.runStep(step, True if(step==self.turntable.nSteps-1) else False)
                self.sceneRight.runStep(step, True if(step==self.turntable.nSteps-1) else False)
                self.turntable.rotate()
                logging.info('Step %d done', step+1)

            logging.info('\033[92m Scanning DONE \033[0m')


if __name__ == "__main__":
    Scanner3D(sys.argv).run()
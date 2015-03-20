#!/usr/bin/env python

import sys, os
import logging
import threading
import getopt
import numpy as np
from gui import Gui, Tkinter
from scanner.config import Config
from scanner.scene import Camera, Scene
from scanner.arduino import Arduino, TurnTable, Laser
from mesher.voxel import VoxelSpace
from mesher import Mesher
from mesher.vtkdelaunay3D import delaunay3D
from mesher.bpa import meshBPA

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

    def toVoxelSpace(self, voxelSize=10):
        space = VoxelSpace(voxelSize)
        for scene in (self.sceneRight, self.sceneLeft):
            for step in scene:
                for point in step:
                    space.addPoint(point)
        return space

    def meshDelaunay3D(self, filename):
        delaunay3D(self.toVoxelSpace().allPoints(), filename)
        self.gui.popUpConfirm('Meshing', 'Meshing with delaunay3D finished')

    def meshBPA(self, filename):
        meshBPA(self.toVoxelSpace().allPoints(), filename)
        self.gui.popUpConfirm('Meshing', 'Meshing with BPA finished')

    def meshToObjFile(self, filename):
        space = self.toVoxelSpace()
        mesher = Mesher(space)
        try:
            mesher.run()
            mesher.writeToObj(filename)
        except:
            logging.exception("\033[31mError during meshing of %s\033[0m" % (filename))
        self.gui.popUpConfirm('Meshing', 'Meshing finished')

    def exportToObjFile(self, filename):
        space = self.toVoxelSpace()
        mesher = Mesher(space)
        mesher.writeToObj(filename)

    def loadConfig(self):
        arduino = Arduino(self.config['Arduino']['port'],
                          True if (self.directory == None) else False)

        self.turntable = TurnTable(self.config['TurnTable']['position'],
                                   self.config['TurnTable']['diameter'],
                                   self.config['TurnTable']['steps'],
                                   arduino)

        self.camera = Camera(self.config['Camera']['port'],
                        (self.config['Camera']['width'], self.config['Camera']['height']),
                        self.config['Camera']['position'],
                        self.config['Camera']['viewangle'],
                        (self.config['File']['save'], self.config['File']['extension']),
                        self.directory)

        # Assume that Laser point to the center of the turntable
        laserRight = Laser(self.config['LaserRight']['pin'], arduino)
        self.sceneRight = Scene("right", self.camera, laserRight, self.turntable)

        laserLeft = Laser(self.config['LaserLeft']['pin'], arduino)
        self.sceneLeft  = Scene("left", self.camera, laserLeft,  self.turntable)    


    def getCalibrationLimits(self, left, right):
        dist = left[0][0] - right[0][0]
        limit = left[0][1]

        for idx in range(len(left)):
            for offset in range(max(0,idx-20),min(len(right),idx+20)):
                x_dist = right[offset][0]-left[idx][0]
                if(x_dist >= 0):
                    x_dist = np.sqrt(np.square(x_dist) + np.square(right[offset][1]-left[idx][1]))
                    if(x_dist<=dist):
                        dist = x_dist
                        limit = min(right[offset][1],left[idx][1])
        return (limit, limit+self.camera.shape[1]/10)

    def getBetween(self, points, limits):
        y = (points.T)[1]
        return points[(limits[0]<y) & (y<limits[1])]

    def linearRegression(self, points):
        x,y = points.T
        param = np.linalg.lstsq(np.vstack([x, np.ones(y.shape)]).T, y)[0]
        return param

    def interserctLines(self, line_1, line_2):
        x = int(round((line_1[1]-line_2[1])/(line_2[0]-line_1[0]),0))
        y = int(round(x*line_1[0]+line_1[1],0))
        return x,y

    def calibration(self):
        logging.info('\033[94m Start calibration (free the table)...\033[0m')
        self.gui.popUpConfirm('Calibration', 'Calibration : free the table and press OK...')
        
        left_line = self.sceneLeft.calibrateBackground()
        right_line = self.sceneRight.calibrateBackground()

        limits = self.getCalibrationLimits(left_line, right_line)
        logging.debug("[CALIBRATION] y limits : %s" %(limits,))
        left_line = self.getBetween(left_line, limits)
        right_line = self.getBetween(right_line, limits)

        left_line = self.linearRegression(left_line)
        right_line = self.linearRegression(right_line)
        logging.debug("[CALIBRATION] left line  : %.2f*x+%.2f" %(left_line[0], left_line[1]))
        logging.debug("[CALIBRATION] right line : %.2f*x+%.2f" %(right_line[0], left_line[1]))

        center = self.interserctLines(left_line, right_line)
        logging.debug("[CALIBRATION] center @ %s" %(center,))

        # Move zero to image center
        center = (center[0] - self.camera.shape[0]/2.0, self.camera.shape[1]/2.0 - center[1])

        self.camera.calibrate(self.turntable, center)
        self.sceneLeft.calibrateLaser(center, -left_line[0])
        self.sceneRight.calibrateLaser(center, -right_line[0])
        logging.info('\033[94m Calibration done. (place your object on the table)\033[0m')
        self.gui.popUpConfirm('Calibration', 'Calibration : Place object and press OK...')


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
            self.calibration()
            self.thread = threading.Thread(target=self.startScan, args=(False,))
            self.thread.start()
        elif(not startThread):
            for step in range(self.turntable.nSteps):
                self.sceneLeft.runStep(step, True if(step==self.turntable.nSteps-1) else False)
                self.sceneRight.runStep(step, True if(step==self.turntable.nSteps-1) else False)
                self.turntable.rotate()
                logging.info('Step %d done', step+1)
            self.arduino.powerOff()

            logging.info('\033[92m Scanning DONE \033[0m')


if __name__ == "__main__":
    Scanner3D(sys.argv).run()

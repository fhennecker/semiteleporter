import  os, sys, logging, getopt, ConfigParser, glob, cv2
import Tkinter, ttk, tkFileDialog, tkMessageBox
import numpy as np
import serial
import threading
import  time
import inspect
import multiprocessing
import shutil

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from douglaspeucker import reduce_pointset

class Arduino:
    def __init__(self, port, isActive=True):
        """ Create a new Arduino object
        port = the serial port for the arduino
        """
        logging.debug("Create Arduino @ port %s" % (port))
        self.isActive = isActive
        if(isActive):
            try:
                self.serialPort = serial.Serial(port, 115200)
                time.sleep(2)
                self.command('P')
                logging.debug("Handshaking with Arduino...")
            except:
                logging.warning("\033[93m No arduino connected / bad serial port.. \033[0m")

    def command(self, cmd):
        #FIXME why arduino fails to response sometimes ?
        response = ''
        if(self.isActive):
            try:
                self.serialPort.write(cmd)
                while(response == ''):
                    response = self.serialPort.read(3)
            except:
                logging.exception("\033[93m Impossible to send the command to the arduino.. \033[0m")

        return response

    def debugMode(self):
        cmd = raw_input('command : ')
        while(cmd not in ('q','quit','e','exit')):
            response = self.command(cmd)
            print("Response : %s" %response)
            cmd = raw_input('command : ')



class Laser:
    def __init__(self, pin, position, yAngle, arduino):
        """ Create a new Laser object
        pin      = number of the pin connected to the arduino
        position = [X, Y, Z], laser position
        yAngle   = angle of the laser plane with YZ plane in radians (left=positive)
        arduino  = the arduino interface
        """

        logging.debug("Create laser @ %s, yAngle=%.2f, pin=%s" % (position, yAngle, pin))

        self.pin      = pin
        self.position = np.array(position, dtype=np.float32)
        self.yAngle   = yAngle
        self.arduino  = arduino
        self.v1       = np.array([0,1,0], dtype=np.float32)
        self.v2       = np.array([-np.sin(self.yAngle), 0, np.cos(self.yAngle)], dtype=np.float32)

    def switch(self, switchOn):
        if(switchOn):
            self.arduino.command(self.pin.upper())
            logging.info('Switching laser on pin %s %s' %(self.pin, 'ON'))
        else:
            self.arduino.command(self.pin.lower())
            logging.info('Switching laser on pin %s %s' %(self.pin, 'OFF'))


class Camera:
    def __init__(self, port, shape, position, rotation, viewAngle, save, processDirectory=None):
        """ Create a new Camera object
        port      = path to the camera
        shape     = (W,H), camera shape Width x Heigth
        position  = [X, Y, Z], camera position
        rotation  = [Rx, Ry, Rz], rotation order (Y->X'->Z")
        viewAngle = <angle>, view angle in degree
        save      = tuple (path where save pictures, extension) or None
        processDirectory = path to the directory of pictures to process (when don't use the scanner)
        """

        logging.debug("Create Camera (%.2f, %.2f) %s @ %s, viewAngle = %.2f, rotation = %s" %(shape[0], shape[1], port, position, viewAngle, rotation))

        self.camId     = int(port[-1])
        self.shape     = shape
        self.position  = np.array(position, dtype=np.float32)
        self.distance  = float(shape[0]/2)/np.tan(np.radians(viewAngle)/2)
        self.rotation  = np.radians(np.array(rotation, dtype=np.float32))
        self.save      = save
        self.processDirectory = processDirectory
        self.buffered  = ("", None)

        # First Rotate around Y/vertical axis
        self.rotationMatrix = np.matrix([[np.cos(self.rotation[1]), 0, -np.sin(self.rotation[1])],
                                         [0                       , 1,  0                       ],
                                         [np.sin(self.rotation[1]), 0,  np.cos(self.rotation[1])]])
        # Then Rotate around X/horizontal axis
        self.rotationMatrix *= np.matrix([[1, 0                       ,  0                       ],
                                          [0, np.cos(self.rotation[0]), -np.sin(self.rotation[0])],
                                          [0, np.sin(self.rotation[0]),  np.cos(self.rotation[0])]])
        # Then Rotate around Z/depth axis
        self.rotationMatrix *= np.matrix([[np.cos(self.rotation[2]), -np.sin(self.rotation[2]), 0],
                                          [np.sin(self.rotation[2]),  np.cos(self.rotation[2]), 0],
                                          [0                      ,  0                        , 1]])

        if(self.processDirectory == None):
            cam = cv2.VideoCapture(self.camId)
            cam.read()
            cam.release()

    def getPicture(self, name, toBuffer=False):
        picture = None;
        if(self.processDirectory == None):
            logging.info('Taking a picture')
 
            if(self.buffered[0] == name):
                picture = self.buffered[1]
            else:
                cam = cv2.VideoCapture(self.camId)
                cam.set(3, self.shape[0])
                cam.set(4, self.shape[1])
                ok, picture = cam.read()
                cam.release()
                if not ok:
                    logging.error("impossible to get a picture from the camera..")
                elif(len(self.save[0]) > 0):
                    cv2.imwrite(os.path.join(self.save[0],name+self.save[1]), picture)
  
                if(toBuffer):
                    self.buffered = (name, np.copy(picture))
        else:
            logging.info('Reading a picture')
            picture = cv2.imread(os.path.join(self.processDirectory, name+self.save[1]))

        return picture


class TurnTable:
    def __init__(self, position, diameter, nSteps, arduino):
        """ Create a new TurnTable object
        position = [X, Y, Z], turntable position
        diameter = <diameter>, turntable diameter
        nSteps   = number of steps for a full turn
        arduino  = the arduino interface
        """

        logging.debug("Create turntable @ %s, diameter = %.2f" % (position, diameter))

        self.position  = np.array(position, dtype=np.float32)
        self.diameter  = diameter
        self.nSteps    = int(nSteps)
        self.arduino   = arduino
        self.stepAngle = 2.0*np.pi/nSteps

    def getRotationMatrix(self, step):
        angle = self.stepAngle*step
        rotationMatrix = np.matrix([[np.cos(angle), 0, -np.sin(angle)],
                                    [0            , 1,              0],
                                    [np.sin(angle), 0,  np.cos(angle)]])
        return rotationMatrix
        

    def rotate(self, step=1):
        logging.info('Rotating the turntable')
        self.arduino.command('T')
        

class Scene:
    def __init__(self, name, camera, laser, turntable):
        """ Create a new scene object
        name   = the name of the scene for pictures names
        camera = the camera object of the scene
        laser  = the laser object of the scene (only on by scene)
        table  = the turntable object of the scene
        """
        self.name       = name
        self.camera     = camera
        self.laser      = laser
        self.turntable  = turntable
        self.imageProcessor = ImageProcessor()
        self.pipeline   = Pipeline(self.imageProcessor.extractPoints,
                                   self.getWorldPoint,
                                   self.simplify)
        self.result = []

    def __iter__(self):
        if(len(self.result) != 0):
            for item in self.result:
                yield item
        else:
            item = self.pipeline.get()
            while(item != None):
                self.result += item
                yield item
                item = self.pipeline.get()

    def simplify(self, points):
        return reduce_pointset(points, 3)

    def calibration(self):
        self.laser.switch(True)
        imgLaserOn = self.camera.getPicture("calibration_"+self.name)
        self.laser.switch(False)
        imgLaserOff = self.camera.getPicture("calibration_off", True)

        self.imageProcessor.setCalibrationMask(imgLaserOn, imgLaserOff)

    def getWorldPoint(self, cameraPoints, step):
        # Intersection of a line and a plane
        # line  : OP = camera.position + lambda * CP
        # plane : OP = laser.position  + alpha * v1  + beta * v2
        #
        # Solve camera.position - laser.position = -lambda * CP + alpha * v1 + beta * v2

        worldPoints = []
        for pixel in cameraPoints:
            # Move zero to image center
            pixel[0]=  pixel[0] - self.camera.shape[0]/2.0
            pixel[1]= -pixel[1] + self.camera.shape[1]/2.0
            # Camera-Ray (CP) vector in camera reference
            CP = np.matrix([pixel[0], pixel[1], self.camera.distance])
            # Rotate Ray in world reference
            CP = self.camera.rotationMatrix * CP.T
            
            # Create system matrix
            systemMatrix = np.matrix([-CP.A1,self.laser.v1,self.laser.v2]).T
            # Inverse system and get solution (can be optimized by only calculate lambda)
            solution = systemMatrix.I * np.matrix(self.camera.position - self.laser.position).T

            point = self.camera.position + solution.A1[0] * CP.T

            # Translate P into turntable reference units and rotate it
            point = self.turntable.getRotationMatrix(step) * (point - self.turntable.position).T

            # Conserve only points on the table
            if(point[1]>0.5 and (point[0]**2+point[2]**2)<(self.turntable.diameter/2)**2):
                worldPoints.append(point.T)
                #logging.debug("%s -> %s" % (str(pixel),str(point.T)))
        
        return worldPoints

    def runStep(self, step, isLastStep):
        if(step == 0):
            self.pipeline.start()

        name = ("%d_%s" %(step, self.name))
        self.laser.switch(True)
        imgLaserOn = self.camera.getPicture(name, False)

        name = ("%d_%s" %(step, "off"))
        self.laser.switch(False)
        imgLaserOff = self.camera.getPicture(name, True)

        self.pipeline.feed((imgLaserOn, imgLaserOff, step))
        if(isLastStep):
            self.pipeline.terminate()


class ImageProcessor:
    def __init__(self):
        """ Create a new ImageProcessor object
        """
        self.calibrationMask = None

    def setCalibrationMask(self, foreground, background):
        mask = self.getLaserMask(foreground, background)
        self.calibrationMask = cv2.bitwise_not(mask)

    def getRGBmask(self, imageDiff, R_threshold=10, GB_threshold=5):
        lower = np.array([0, 0, R_threshold], dtype=np.uint8)
        upper = np.array([GB_threshold, GB_threshold, 255], dtype=np.uint8)
        mask = cv2.inRange(imageDiff, lower, upper)
        return cv2.GaussianBlur(mask,(3,3),0)

    def getHSVmask(self, imageDiff, luminosity=20):
        image = cv2.cvtColor(imageDiff, cv2.COLOR_BGR2HSV)

        lower = np.array([0, 10, luminosity], dtype=np.uint8)
        upper = np.array([10, 255, 255], dtype=np.uint8)
        mask1 = cv2.inRange(image, lower, upper)

        lower = np.array([170, 10, luminosity], dtype=np.uint8)
        upper = np.array([180, 255, 255], dtype=np.uint8)
        mask2 = cv2.inRange(image, lower, upper)

        return np.bitwise_or(mask1, mask2)

    def getLaserMask(self, foreground, background):
        imageDiff = np.array(foreground, dtype=np.int16) - background
        imageDiff = np.array(imageDiff.clip(0, 255), dtype=np.uint8)
        mask = cv2.bitwise_or(self.getRGBmask(imageDiff), self.getHSVmask(imageDiff))
        mask = cv2.GaussianBlur(mask,(3,3),0)
        return cv2.inRange(mask, np.array([250]), np.array([255]))
        

    def massCenter(self, image):
        points = []
        for line in range(image.shape[0]):
            moments = cv2.moments(image[line,:,2])
            if(moments['m00'] != 0):
                points.append([round(moments['m01']/moments['m00']), line])

        return points

    def extractPoints(self, imgLaserOn, imgLaserOff):
        mask = cv2.bitwise_and(self.getLaserMask(imgLaserOn, imgLaserOff), self.calibrationMask)
        res = cv2.bitwise_and(imgLaserOn, imgLaserOn, mask=mask)
        res = self.massCenter(res)
        return res


class EndOfProcessing:
    pass


class PipelineStage(multiprocessing.Process):
    def __init__(self, method, in_queue, out_queue):
        """ Create a new PipelineStage object
        method    = the method to apply
        in_queue  = the queue of inputs jobs
        out_queue = the queue of results
        """
        super(PipelineStage, self).__init__()
        self.method    = method
        self.in_queue  = in_queue
        self.out_queue = out_queue

    def run(self):
        args = self.in_queue.get()

        while(args != EndOfProcessing):
            try:
                nbrOfArgs = len(inspect.getargspec(self.method).args)-1
                res = (self.method(*args[:nbrOfArgs]),)+args[nbrOfArgs:]
                logging.debug("Process '%s' put a result" %(self.method.__name__))
                self.out_queue.put(res)
            except:
                logging.error("Bad args format in PipelineStage '%s'" %(self.method.__name__))
            args = self.in_queue.get()
        self.out_queue.put(EndOfProcessing)
        logging.debug("Process '%s' down" %(self.method.__name__))


class Pipeline:
    def __init__(self, *methods):
        """ Create a new Pipeline object
        output  = the output container of the pipeline
        methods = all methods applied by the pipeline in the same order
        """
        self.in_queue = multiprocessing.Queue()
        self.out_queue = multiprocessing.Queue()
        self.stages   = []

        in_queue = self.in_queue
        out_queue = None
        for order in range(len(methods)):
            if(order == len(methods)-1):
                self.stages.append(PipelineStage(methods[order], in_queue, self.out_queue))
            else:
                out_queue = multiprocessing.Queue()
                self.stages.append(PipelineStage(methods[order], in_queue, out_queue))
                in_queue = out_queue

    def get(self):
        item = self.out_queue.get()
        if(item == EndOfProcessing):
            item = None
        return item
            
    def start(self):
        map(PipelineStage.start, self.stages)

    def feed(self, arg):
        self.in_queue.put(arg)

    def terminate(self):
        self.feed(EndOfProcessing)


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


#---------------------------------------------------------

class Tab(Tkinter.Frame):
    def __init__(self, rootTab, title=""):
        """ Create a new 'abstract' Tab object
        rootTab = the Notebook reference
        title   = the name of the tab
        """
        self.rootTab = rootTab
        Tkinter.Frame.__init__(self, self.rootTab, width=800, height=600)
        self.rootTab.add(self, text=title)


class SetupTab(Tab):
    def __init__(self, rootTab, config):
        """ Create a new SetupTab object
        rootTab = the Notebook reference
        config  = the reference to the Config object from the Scanner
        """
        Tab.__init__(self, rootTab, "Setup")
        self.config  = config
        self.entries = dict()

        for i in range(6):
            self.rowconfigure(i, weight=1)
        for i in range(3):
            self.columnconfigure(i, weight=1)

        self.createSectionFrame("File").grid(row=0, column=0, columnspan=3)
        self.createSectionFrame("Arduino").grid(row=1, column=0, columnspan=3)
        self.createSectionFrame("Camera").grid(row=2, column=0, columnspan=3)
        self.createSectionFrame("LaserLeft").grid(row=3, column=0, columnspan=3)
        self.createSectionFrame("LaserRight").grid(row=4, column=0, columnspan=3)
        self.createSectionFrame("TurnTable").grid(row=5, column=0, columnspan=3)
        Tkinter.Button(self, text="Open", command=self.openConfigFile).grid(row=6, column=0, sticky='e')
        Tkinter.Button(self, text="Load", command=self.loadConfigFile).grid(row=6, column=1)
        Tkinter.Button(self, text="Save", command=self.saveConfigFile).grid(row=6, column=2, sticky='w')

    def createSectionFrame(self, section):
        frame = Tkinter.LabelFrame(self, text=section, font=("bold"))

        self.entries[section] = dict()
        line = 0
        for option in self.config[section]:
            value = self.config.getToStr(section, option)
            if(type(value) == list):
                varList = []
                Tkinter.Label(frame, text=option+" :").grid(row=line, column=0)
                line += 1
                for item,letter,col in zip(value, range(123-len(value),123), range(0,2*len(value),2)):
                    Tkinter.Label(frame, text=(chr(letter).upper()+" :")).grid(row=line, column=col)
                    varList.append(Tkinter.StringVar(frame, item))
                    Tkinter.Entry(frame, background="white", textvariable=varList[-1]).grid(row=line, column=col+1)
                self.entries[section][option] = varList
            else:
                Tkinter.Label(frame, text=option).grid(row=line, column=0)
                self.entries[section][option] = Tkinter.StringVar(frame, value)
                if(option == "port"):
                    path = self.entries[section][option].get()[:-1]+"*"
                    ttk.Combobox(frame, textvariable=self.entries[section][option], values=glob.glob(path), state='readonly', background="white").grid(row=line, column=1, padx=5, pady=5)
                else:
                    Tkinter.Entry(frame, background="white", textvariable=self.entries[section][option]).grid(row=line, column=1)
            line += 1
        return frame

    def refresh(self):
        for section in self.entries:
            for option in self.entries[section]:
                res = self.entries[section][option]
                if(type(res) == list):
                    for entry,idx in zip(res,range(len(res))):
                        entry.set(self.config[section][option][idx])
                else:
                    res.set(self.config[section][option])

    def openConfigFile(self):
        ext = None
        filename = None
        while(ext !=".cfg" and filename != ''):
            filename = tkFileDialog.askopenfilename(defaultextension=".cfg")
            ext = os.path.splitext(filename)[-1]
        if(filename != ''):
            self.config.load(filename)
            self.refresh()

    def loadConfigFile(self):
        logging.info("Loading Gui config to Config object")
        for section in self.entries:
            for option in self.entries[section]:
                res = self.entries[section][option]
                if(type(res) == list):
                    res = [res[0].get(),res[1].get(),res[2].get()]
                    self.config[section][option] = np.array(res, dtype=np.float32)
                else:
                    try:
                        self.config[section][option] = float(res.get())
                    except:
                        self.config[section][option] = res.get()

    def saveConfigFile(self):
        self.loadConfigFile()
        self.config.save()


class ViewerTab(Tab):
    def __init__(self, rootTab, scanner):
        """ Create a new ViewerTab object
        rootTab = the Notebook reference
        scanner = the Scanner reference
        """
        Tab.__init__(self, rootTab, "Viewer")

        self.scanner = scanner
        self.graph   = None
        self.axis    = None
        self.createGraph()
        self.createOptions()

    def createGraph(self, init=True):
        if(init):
            self.figure = plt.figure()
            self.graph = FigureCanvasTkAgg(self.figure, master=self)
            self.graph.get_tk_widget().grid(row=0, column=0)
            self.axis = self.figure.add_subplot(111, projection='3d')
        else:
            self.axis.clear()
        self.axis.set_xlabel('X axis')
        self.axis.set_xlim3d(-250,250)
        self.axis.set_ylabel('Y axis')
        self.axis.set_ylim3d(-250,250)
        self.axis.set_zlabel('Z axis')
        self.axis.set_zlim3d(0,500)
        self.graph.show()

    def createOptions(self):
        frame = Tkinter.LabelFrame(self, text="Options", font=("bold"))
        frame.grid(row=0, column=1)
        Tkinter.Button(frame, text="Start", command=self.start).grid(row=0, column=0)
        Tkinter.Button(frame, text="Export", command=self.export).grid(row=1, column=0)

    def export(self):
        ext = None
        filename = None
        while(ext!=".obj" and filename != ''):
            filename = tkFileDialog.asksaveasfilename(defaultextension=".obj")
            ext = os.path.splitext(filename)[-1]
        if(filename != ""):
            self.scanner.exportToObjFile(filename)

    def start(self):
        self.scanner.startScan()
        self.plot()

    def plot(self, scene=None, lock=None):
        if(lock == None):
            self.createGraph(False)
            logging.info("Start plotting")
            lock = threading.Lock()
            thread_left = threading.Thread(target=self.plot, args=(self.scanner.sceneLeft, lock))
            thread_right = threading.Thread(target=self.plot, args=(self.scanner.sceneRight, lock))
            thread_left.start()
            thread_right.start()
        else:
            for item in scene:
                points = np.array(item).T
                if(len(points) != 0):
                    lock.acquire()
                    self.axis.scatter(points[0], points[2], points[1], c='b', marker='.', s=2)
                    self.graph.draw()
                    lock.release()



class Gui(Tkinter.Tk):
    def __init__(self, scanner):
        """ Create a new Gui object
        scanner = reference to the Scanner object
        """
        logging.info("Starting Gui")
        Tkinter.Tk.__init__(self, None)

        self.title("Scanner 3D")
        self.rootTab   = ttk.Notebook(self)
        self.rootTab.pack(fill='both',expand=True)
        self.viewerTab = ViewerTab(self.rootTab, scanner)
        self.setupTab  = SetupTab(self.rootTab, scanner.config)

        self.protocol('WM_DELETE_WINDOW', exit)

    def popUpConfirm(self, title, info):
        tkMessageBox.showinfo(title, info)
        self.update()

    def run(self):
        self.mainloop()

    def exit(self):
        self.destroy()
        self.quit()


if(__name__ == "__main__"):
    myScanner3D = Scanner3D(sys.argv)
    myScanner3D.run()

import  os, sys, logging, getopt, ConfigParser, cv2
import Tkinter
import numpy as np

import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class Arduino:
    def __init__(self, port):
        """ Create a new Arduino object
        port = the serial port for the arduino
        """
        logging.debug("Create Arduino @ %s" % (port))
        self.serialPort = serial.Serial(port, 9600)
        logging.debug("Booting Arduino...")
        self.sleep(3)

    def command(self, cmd):
        self.serialPort.write(cmd)
        while self.serialPort.read(1) != cmd:
            pass
        


class Laser:
    def __init__(self, position, yAngle, arduino):
        """ Create a new Laser object
        position = [X, Y, Z], laser position
        yAngle   = angle of the laser plane with YZ plane in degree (left=positive)
        arduino  = the arduino interface
        """

        logging.debug("Create laser @ %s, yAngle=%.2f" % (position, yAngle))

        self.position = position
        self.yAngle   = np.radians(yAngle)
        self.arduino  = arduino
        self.v1  = np.array([0,1,0], dtype=np.float32)
        self.v2  = np.array([-np.sin(self.yAngle), 0, np.cos(self.yAngle)], dtype=np.float32)

    def switch(self, switchOn):
        #FIXME control the laser on/off here
        logging.debug('Switching laser %s' %('ON' if switchOn else 'OFF'))
        pass


class Camera:
    def __init__(self, shape, position, rotation, viewAngle, pictureDirectory=""):
        """ Create a new Camera object
        shape     = (W,H), camera shape Width x Heigth
        position  = [X, Y, Z], camera position
        rotation  = [Rx, Ry, Rz], rotation order (Y->X'->Z")
        viewAngle = <angle>, view angle in degree
        pictureDirectory = path to the directory of pictures to process (when don't use the scanner)
        """

        logging.debug("Create Camera (%.2f, %.2f) @ %s, viewAngle = %.2f, rotation = %s" %(shape[0], shape[1], position, viewAngle, rotation))

        self.shape     = shape
        self.position  = position
        self.distance  = (shape[0]/2)/np.tan(np.radians(viewAngle)/2)
        self.viewAngle = viewAngle
        self.rotation  = np.radians(rotation)
        self.pictures  = []

        if(pictureDirectory != ""):
            self.pictures = [os.path.join(pictureDirectory, f) for f in os.listdir(pictureDirectory)]
            self.pictures.sort()

        # First Rotate around Y/vertical axis
        self.rotationMatrix = np.matrix([[np.cos(rotation[1]), 0, -np.sin(rotation[1])],
                                         [0                  , 1,  0                  ],
                                         [np.sin(rotation[1]), 0,  np.cos(rotation[1])]])
        # Then Rotate around X/horizontal axis
        self.rotationMatrix *= np.matrix([[1, 0                  ,  0                  ],
                                          [0, np.cos(rotation[0]), -np.sin(rotation[0])],
                                          [0, np.sin(rotation[0]),  np.cos(rotation[0])]])
        # Then Rotate around Z/depth axis
        self.rotationMatrix *= np.matrix([[np.cos(rotation[2]), -np.sin(rotation[2]), 0],
                                          [np.sin(rotation[2]),  np.cos(rotation[2]), 0],
                                          [0                  ,  0                  , 1]])

    def getPicture(self):
        picture = None;

        if(len(self.pictures) == 0):
            logging.debug('Taking a picture')
            #FIXME control the camera to take a picture here
            pass
        else:
            logging.debug('Reading a picture')
            self.pictures.append(self.pictures[0])
            picture = cv2.imread(self.pictures.pop(0))

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

        self.position  = position
        self.diameter  = diameter
        self.nSteps    = nSteps
        self.arduino   = arduino
        self.stepAngle = 2.0*np.pi/nSteps

    def getRotationMatrix(self, step):
        angle = self.stepAngle*step
        rotationMatrix = np.matrix([[np.cos(angle), 0, -np.sin(angle)],
                                    [0            , 1,              0],
                                    [np.sin(angle), 0,  np.cos(angle)]])
        return rotationMatrix
        

    def rotate(self, step=1):
        logging.debug('Rotating the turntable')
        #FIXME control the stepper motor to rotate here
        

class Scene:
    def __init__(self, camera, laser, turntable):
        """ Create a new scene object
        camera = the camera object of the scene
        laser  = the laser object of the scene (only on by scene)
        table  = the turntable object of the scene
        """
        self.camera     = camera
        self.laser      = laser
        self.turntable  = turntable
        self.imageProcessor = ImageProcessor()
        self.calibMask  = None

    def calibration(self):
        self.laser.switch(True)
        imgLaserOn = self.camera.getPicture()
        self.laser.switch(False)
        imgLaserOff = self.camera.getPicture()

        self.calibMask = self.imageProcessor.substract(imgLaserOn, imgLaserOff)
        self.calibMask = self.imageProcessor.filterNoise(self.calibMask)
        self.calibMask = (self.calibMask-1)/255

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
            if(point[1]>0 and (point[0]**2+point[2]**2)<(self.turntable.diameter/2)**2):
                worldPoints.append(point.T)
                #logging.debug("%s -> %s" % (str(pixel),str(point.T)))
        
        return worldPoints

    def get3dView(self, step):
        self.laser.switch(True)
        imgLaserOn = self.camera.getPicture()#*self.calibMask
        self.laser.switch(False)
        imgLaserOff = self.camera.getPicture()

        cameraPoints = self.imageProcessor.extractPoints(imgLaserOn, imgLaserOff)
        return self.getWorldPoint(cameraPoints, step)


class ImageProcessor:
    def __init__(self):
        """ Create a new ImageProcessor object
        """

    def substract(self, foreground, background):
        image = np.array(foreground, dtype=np.int16) - background
        image[:,:,:2] = 0
        image = np.array(image.clip(0), dtype=np.uint8)
        return image

    def filterNoise(self, image):
        image = cv2.GaussianBlur(image,(5,5),0)
        ret, image = cv2.threshold(image, 27, 255, cv2.THRESH_TOZERO)
        return image

    def massCenter(self, image):
        points = []

        for line in range(image.shape[0]):
            moments = cv2.moments(image[line,:,2])
            if(moments['m00'] != 0):
                points.append([round(moments['m01']/moments['m00']), line])

        return points

    def extractPoints(self, laserOn, laserOff):
        res = self.substract(laserOn, laserOff)
        res = self.filterNoise(res)
        res = self.massCenter(res)
        return res


class Scanner3D(Tkinter.Tk):
    def __init__(self, args):
        """ Create a new Scanner3D object
        args = arguments passed in the command line
        """
        self.configFile = "default.cfg"
        self.directory  = ""
        self.logLevel   = logging.WARNING
        self.camera     = None
        self.sceneLeft  = None
        self.sceneRight = None
        self.turntable  = None
    
        self.parseArgv(args)
        self.loadConfig()


    def usage(self, args):
        print("Usage : %s <options>" % args[0])
        print("Available options:")
        print("  --help      , -h             : print this help")
        print("  --config    , -c <filename>  : use filename as configuration file (default=default.cfg)")
        print("  --processing, -p <directory> : use directory as the path to the directory of pictures to process (when you don't use the scanner)")
        print("  --loglevel  , -l <loglevel>  : set logelevel (default=WARNING)")


    def parseArgv(self,args):
        """ This method parse command line """
        try:
            opts, arguments = getopt.getopt(args[1:],"c:l:p:h",["file=", "loglevel=", "directory=", "help"])
        except getopt.GetoptError as err:
            logging.error(str(err))
            self.usage(args)
            sys.exit(2)

        for o,a in opts:
            if(o in ("-h", "--help")):
                self.usage(args)
                sys.exit()
            elif(o in ("-c", "--config")):
                self.cfgFilename = a
            elif(o in ("-l", "--loglevel")):
                try:
                    self.logLevel = getattr(logging, a.upper())
                except:
                    logging.error("Invalid loglevel")
                    sys.exit(2)
            elif(o in ("-p", "--processing")):
                self.directory = a
            else:
                assert False, "Unknown option"

        logging.getLogger().setLevel(self.logLevel)


    def loadConfig(self):
        """ This method read the config file """
        if(not os.path.exists(self.configFile)):
            logging.error("File %s don't exist" % self.configFile)
            sys.exit(2)
            
        logging.info('Parsing %s configuration file ...' % self.configFile)
        config = ConfigParser.ConfigParser()
        config.read(self.configFile)

        # Define setup
        try:
            self.imageExtension = config.get('File', 'extension')

            self.camera = Camera((float(config.get('Camera', 'width')), float(config.get('Camera', 'height'))),
                               np.array(config.get('Camera', 'position').split(','), dtype=np.float32),
                               np.array(config.get('Camera', 'rotation').split(','), dtype=np.float32),
                                  float(config.get('Camera', 'viewAngle')),
                               self.directory)

            arduino = Arduino(config.get('Arduino', 'serial'))

            self.turntable = TurnTable(np.array(config.get('TurnTable', 'position').split(','), dtype=np.float32),
                                       float(config.get('TurnTable', 'diameter')),
                                       int(config.get('TurnTable', 'steps')),
                                       arduino)

            # Assume that Laser point to the center of the turntable
            pos = np.array(config.get('LaserRight', 'position').split(','), dtype=np.float32)
            laserRight = Laser(pos, np.degrees(np.arctan(pos[0]/self.turntable.position[2])), arduino)
            self.sceneRight = Scene(self.camera, laserRight, self.turntable)

            pos = np.array(config.get('LaserLeft', 'position').split(','), dtype=np.float32)
            laserLeft = Laser(pos, np.degrees(np.arctan(pos[0]/self.turntable.position[2])), arduino)
            self.sceneLeft  = Scene(self.camera, laserLeft,  self.turntable)    

        except:
            logging.error('Syntax error in %s', self.configFile)
            sys.exit(2)

    def run(self):
        logging.info('\t\033[92m----- Start scanning -----\033[0m')

        points = []
        logging.info('\033[94m Calibration : free the table and press ENTER...\033[0m')
        raw_input('')
        self.sceneLeft.calibration()
        self.sceneRight.calibration()
        logging.info('\033[94m Calibration : done, place your object on the table and press ENTER...\033[0m')
        raw_input('')

        for step in range(self.turntable.nSteps):
            points += self.sceneLeft.get3dView(step)
            points += self.sceneRight.get3dView(step)
            self.turntable.rotate()
            logging.info('Step %d done', step+1)

        logging.info('\033[92m Scanning done \033[0m')
        self.plot(points)

    def plot(self, points):
        points = np.array(points).T
        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(points[0], points[2], points[1], c='b', marker='.', s=2)
        ax.set_xlabel('X axis')
        ax.set_xlim3d(-250,250)
        ax.set_ylabel('Y axis')
        ax.set_ylim3d(-250,250)
        ax.set_zlabel('Z axis')
        ax.set_zlim3d(0,500)
        plt.show()
        


if(__name__ == "__main__"):
    myScanner3D = Scanner3D(sys.argv)
    myScanner3D.run()

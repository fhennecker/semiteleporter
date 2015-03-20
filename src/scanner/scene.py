import os
import logging
import cv2
import numpy as np
from .image import ImageProcessor
from .pipeline import Pipeline
from .douglaspeucker import reduce_pointset
from mesher.voxel import Point


class Camera:
    def __init__(self, port, shape, position, viewAngle, save, processDirectory=None):
        """ Create a new Camera object
        port      = path to the camera
        shape     = (W,H), camera shape Width x Heigth
        position  = [X, Y, Z], camera position
        rotation  = [Rx, Ry, Rz], rotation order (Y->X'->Z")
        viewAngle = <angle>, view angle in degree
        save      = tuple (path where save pictures, extension) or None
        processDirectory = path to the directory of pictures to process (when don't use the scanner)
        """

        logging.debug("Create Camera %s (%.2f, %.2f) @ %s, viewAngle = %.2f" %(port, shape[0], shape[1], position, viewAngle))

        self.camId     = int(port[-1])
        self.shape     = shape
        self.position  = np.array(position, dtype=np.float32)
        self.distance  = float(shape[0]/2)/np.tan(np.radians(viewAngle)/2)
        self.rotation  = None
        self.save      = save
        self.processDirectory = processDirectory
        self.buffered  = ("", None)
        self.rotationMatrix = np.matrix(np.eye(3))

        if(self.processDirectory == None):
            cam = cv2.VideoCapture(self.camId)
            cam.read()
            cam.release()

    def calibrate(self, turnTable, (x,y)):
        ''' Compute Camera rotation from expected and observed turnTable (x,y) center
            Rotation around the Z-axis is not supported
        '''
        # Unit vector pointing to the original turntable center
        origUnitVect = turnTable.position - self.position
        origUnitVect /= np.linalg.norm(origUnitVect)

        # Unit vector pointing to the current turntable center
        currentUnitVect = np.array([x,y,self.distance], dtype=float)
        currentUnitVect /= np.linalg.norm(currentUnitVect)

        Yzx = self.getAngle(
            currentUnitVect[0], # x"
            origUnitVect[0],    # x
            -origUnitVect[2])   # -z        
        logging.debug('Yzx = %5.2f' % np.degrees(Yzx))

        Xyz = self.getAngle(
            currentUnitVect[1], # y"
            origUnitVect[1],    # y
            -origUnitVect[0]*np.sin(Yzx)-origUnitVect[2]*np.cos(Yzx)) # x*sin(Yzx)+z*cos(Yzx)
        logging.debug('Xyz = %5.2f' % np.degrees(Xyz))

        # Rotate first around Y/vertical axis, then X/horizontal axis
        self.rotationMatrix = np.matrix([[ np.cos(Yzx),             0,           -np.sin(Yzx)            ],
                                         [-np.sin(Xyz)*np.sin(Yzx), np.cos(Yzx), -np.sin(Xyz)*np.cos(Yzx)],
                                         [ np.cos(Xyz)*np.sin(Yzx), np.sin(Xyz),  np.cos(Xyz)*np.cos(Yzx)]])


    def getAngle(self, a, b, c):
        ''' Solve a = b*cos(angle)+c*sin(angle) equation with angle [-pi/2:pi/2]
        '''
        # Above equation is equivalent to:
        #     a/norm([b,c]) = cos(u)*cos(angle)+ sin(u)*sin(angle)
        u = np.arcsin(c/np.linalg.norm((b,c)))
        # or  a/norm([b,c]) = cos(u-angle)
        # or  angle = u - acos(a/norm([b,c])
        angle = u-np.arccos(a/np.linalg.norm((b,c)))
        return ((angle + np.pi/2) % np.pi) - np.pi/2


    def getPicture(self, name, toBuffer=False):
        picture = None
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


class Scene:
    def __init__(self, name, camera, laser, turnTable):
        """ Create a new scene object
        name   = the name of the scene for pictures names
        camera = the camera object of the scene
        laser  = the laser object of the scene (only on by scene)
        table  = the turntable object of the scene
        """
        self.name       = name
        self.camera     = camera
        self.laser      = laser
        self.turnTable  = turnTable
        self.imageProcessor = ImageProcessor()
        self.pipeline   = Pipeline(self.getWorldPoint)
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

    def calibrateBackground(self):
        self.laser.switch(True)
        imgLaserOn = self.camera.getPicture("calibration_"+self.name)
        self.laser.switch(False)
        imgLaserOff = self.camera.getPicture("calibration_off", True)

        return self.imageProcessor.setCalibrationMask(imgLaserOn, imgLaserOff)

    def calibrateLaser(self, (x,y), m):
        ''' Compute Laser position and angle from the slope of the laser line on the
            screen and turntable position. This method should be executed after Camera
            calibration to make sure that its rotation matrix is correctly set.
            turnTable = turntable object
            (x,y)     = position of the turntable center (laser line should intersect it)
            m         = slope of the laser line (y=mx+p) on the screen
        '''

        # Define a plane based on the laser line on the screen ...
        laserLineVect = np.array([1, m, 0], dtype=float)
        # ... and the ray pointing to the turntable center (laser line should intersect it)
        turnTableVect = np.array([x,y,self.camera.distance], dtype=float)
        # A plane is described by the following equation a*x+b*y+c*z+d=0
        # (a,b,c) is the cross product of the two director vectors define above
        abcVect = np.cross(laserLineVect, turnTableVect)
        # Rotate vector in world reference as they were defined in Camera reference
        abcVect = (self.camera.rotationMatrix * np.matrix(abcVect).T).A1
        # d is defined by forcing the plane to pass by the camera position
        d       = -np.dot(abcVect, self.camera.position)
        # Intersection of that plane with the Xaxis (a*x+b*turnTable.y+c*0+d=0) is the laser position
        laserX     = -(d+abcVect[1]*self.turnTable.position[1])/abcVect[0]
        # Compute laser angle in (radian) assuming it intersects the turntable center
        laserAngle = np.arctan(laserX/self.turnTable.position[2])

        self.laser.calibrate(np.array([laserX, self.camera.position[1], 0.0], dtype=np.float32), laserAngle)


    def getWorldPoint(self, imgLaserOn, imgLaserOff, step):
        # Intersection of a line and a plane
        # line  : OP = camera.position + lambda * CP
        # plane : OP = laser.position  + alpha * v1  + beta * v2
        #
        # Solve camera.position - laser.position = -lambda * CP + alpha * v1 + beta * v2

        cameraPoints = self.imageProcessor.extractPoints(imgLaserOn, imgLaserOff)

        worldPoints = []
        maxRadius = (self.turnTable.diameter/2)**2

        rotMatrix = self.turnTable.getRotationMatrix(step)

        for pixel in cameraPoints:
            pixel2D = tuple(map(int, pixel))

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

            # Normal is laser-point translated in turntable system
            normal = rotMatrix * (self.laser.position - point).T

            # Translate P into turntable reference units and rotate it
            point = rotMatrix * (point - self.turnTable.position).T

            p = Point()

            # Conserve only points on the table
            if point[1] > 0.5 and (point[0]**2 + point[2]**2) < maxRadius:
                x, z, y = np.array(point.T)[0]
                nx, ny, nz = np.array(normal.T)[0]
                # TODO: verify color channels order and indexes order
                b, g, r = imgLaserOff[pixel2D[1]][pixel2D[0]]
                worldPoints.append(Point(
                    x=x, y=y, z=z, 
                    r=r, g=g, b=b, 
                    nx=nx, ny=ny, nz=nz
                ))
                #logging.debug("%s -> %s" % (str(pixel),str(point.T)))
        
        return reduce_pointset(worldPoints, 2)

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

import os
import logging
import cv2
import numpy as np
from .image import ImageProcessor
from .pipeline import Pipeline
from .douglaspeucker import reduce_pointset


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
                                   self.getWorldPoint)
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
                worldPoints.append(np.array(point.T)[0])
                #logging.debug("%s -> %s" % (str(pixel),str(point.T)))
        
        return reduce_pointset(worldPoints, 5)

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

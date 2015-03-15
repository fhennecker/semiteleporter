import numpy as np
import cv2
import time


class ImageProcessor:
    def __init__(self):
        """ Create a new ImageProcessor object
        """
        self.calibrationMask = None

    def setCalibrationMask(self, foreground, background):
        mask = self.getLaserMask(foreground, background)
        self.calibrationMask = cv2.bitwise_not(mask)
        cv2.imwrite("calib_%d.png" %time.time(), self.calibrationMask)

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
        return np.array(points)

    def getYBeetween(self, points, limit):
        y = (points.T)[1]
        return points[(limit[0]<y) & (y<limit[1])]

    def linearRegression(self, points):
        x,y = points.T
        param = np.linalg.lstsq(np.array([y, np.ones(y.shape)]).T, x)[0]
        return param

    def interserctLines(self, line_1, line_2):
        y = (line_1[1]-line_2[1])/(line_2[0]-line_1[0])
        x = y*line_1[0]+line_1[1]
        return x,y

    def extractPoints(self, imgLaserOn, imgLaserOff):
        mask = cv2.bitwise_and(self.getLaserMask(imgLaserOn, imgLaserOff), self.calibrationMask)
        res = cv2.bitwise_and(imgLaserOn, imgLaserOn, mask=mask)
        res = self.massCenter(res)
        return res

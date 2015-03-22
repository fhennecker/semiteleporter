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
        mask = cv2.bitwise_and(foreground,foreground,mask = mask)
        return self.massCenter(mask)

    def getRGBmask(self, imageDiff, R_threshold=20, GB_threshold=5):
        lower = np.array([0, 0, R_threshold], dtype=np.uint8)
        upper = np.array([GB_threshold, GB_threshold, 255], dtype=np.uint8)
        return cv2.inRange(imageDiff, lower, upper)

    def getHSVmask(self, imageDiff, luminosity=20):
        image = cv2.cvtColor(imageDiff, cv2.COLOR_BGR2HSV)

        lower = np.array([0, 170, luminosity], dtype=np.uint8)
        upper = np.array([10, 255, 255], dtype=np.uint8)
        mask = cv2.inRange(image, lower, upper)

        lower = np.array([170, 170, luminosity], dtype=np.uint8)
        upper = np.array([180, 255, 255], dtype=np.uint8)
        mask = cv2.bitwise_or(cv2.inRange(image, lower, upper), mask)

        # high brightness, red is blue (cyan)
        lower = np.array([80, 0, 200], dtype=np.uint8)
        upper = np.array([100, 255, 255], dtype=np.uint8)
        mask = cv2.bitwise_or(cv2.inRange(image, lower, upper), mask)
        return mask

    def getLaserMask(self, foreground, background):
        imageDiff = np.array(foreground, dtype=np.int16) - np.array(background, dtype=np.int16)
        imageDiff = np.array(imageDiff.clip(0, 255), dtype=np.uint8)
        imageDiff = cv2.medianBlur(imageDiff,3)
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

    def extractPoints(self, imgLaserOn, imgLaserOff):
        mask = cv2.bitwise_and(self.getLaserMask(imgLaserOn, imgLaserOff), self.calibrationMask)
        res = cv2.bitwise_and(imgLaserOn, imgLaserOn, mask=mask)
        res = self.massCenter(res)
        return res

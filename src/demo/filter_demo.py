import cv2
import numpy as np
from matplotlib import pyplot as plt

def dia(img):
    color = ('b','g','r')
    for i,col in enumerate(color):
        histr = cv2.calcHist([img],[i],None,[256],[0,256])
        plt.plot(histr,color = col)
        plt.xlim([0,256])
    plt.show()

def color():
    img_off = cv2.imread('./lampe/65_off.png')
    img_on = cv2.imread('./lampe/65_right.png')

    img = np.array((np.array(img_on, dtype=np.int16)-np.array(img_off, dtype=np.int16)).clip(0,255), dtype=np.uint8)
    img = cv2.medianBlur(img,3)
    cv2.imshow("soustracted",cv2.resize(img, (img.shape[1]/2,img.shape[0]/2)))
    cv2.waitKey(0)

    lower = np.array([0, 0, 20], dtype=np.uint8)
    upper = np.array([5, 5, 255], dtype=np.uint8)
    mask0 = cv2.inRange(img, lower, upper)
    cv2.imshow("color_threshold_red",cv2.resize(mask0, (img.shape[1]/2,img.shape[0]/2)))
    cv2.waitKey(0)

    img_hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    lower = np.array([0, 170, 20], dtype=np.uint8)
    upper = np.array([10, 255, 255], dtype=np.uint8)
    mask1 = cv2.inRange(img_hsv, lower, upper)

    lower = np.array([170, 170, 20], dtype=np.uint8)
    upper = np.array([180, 255, 255], dtype=np.uint8)
    mask2 = cv2.inRange(img_hsv, lower, upper)

    mask = np.bitwise_or(mask1, mask2)
    cv2.imshow("hsv_threshold_low_brightness",cv2.resize(mask, (mask.shape[1]/2,mask.shape[0]/2)))
    cv2.waitKey(0)

    lower = np.array([80, 0, 200], dtype=np.uint8)
    upper = np.array([100, 255, 255], dtype=np.uint8)
    mask3 = cv2.inRange(img_hsv, lower, upper)
    cv2.imshow("hsv_threshold_high_brightness",cv2.resize(mask3, (mask3.shape[1]/2,mask3.shape[0]/2)))
    cv2.waitKey(0)

    mask = np.bitwise_or(mask, mask3)
    mask = np.bitwise_or(mask0, mask)
    mask = cv2.GaussianBlur(mask,(3,3),0)
    mask = cv2.inRange(mask, np.array([250]), np.array([255]))

    res = cv2.bitwise_and(img_on, img_on, mask=mask)
    tmp = np.zeros(res.shape)

    for line in range(res.shape[0]):
        moments = cv2.moments(res[line,:,2])
        if(moments['m00'] != 0):
            tmp[line][round(moments['m01']/moments['m00'])] = [0,255,0]


    cv2.imshow("hsv_or_color",cv2.resize(mask, (mask.shape[1]/2,mask.shape[0]/2)))
    cv2.waitKey(0)
    cv2.imshow("result",cv2.resize(tmp, (res.shape[1]/2,res.shape[0]/2)))
    cv2.waitKey(0)

if("__main__" == __name__):

    color()


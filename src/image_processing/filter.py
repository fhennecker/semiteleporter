from sys import argv
import cv2
import numpy as np


def substract(sub_path, base_path, noise=20):
    # this method substract base from sub
    res = cv2.imread(sub_path)
    base = cv2.imread(base_path)

    for line in range(res.shape[0]):
        for pixel in range(res.shape[1]):

            if(((int(res[line][pixel][2]) - int(base[line][pixel][2])) < noise)):
                res[line][pixel][2] = 0

            res[line][pixel][0] = 0
            res[line][pixel][1] = 0

    return res



def filterNoise(img):
    # this method apply a filter to delete alone pixels
    img = cv2.GaussianBlur(img,(5,5),0)
    ret, img = cv2.threshold(img, 63, 255, cv2.THRESH_TOZERO)
    return img


def massCenter(img, output, limit=None):
    # this method search the mass center of the red color by line in each area delimited by limit
    height,x,y = 0,0,0
    parts = []
    res = [[],[]]

    if(limit == None):
        height = img.shape[0]
    else:
        height = len(limit)

    for line in range(height):
        if(limit == None):
            x,y = img.shape[1], line
            parts = [img[y,:,2]]
        else:
            x,y = limit[line]
            parts = [img[y,:x,2], img[y,x:,2]]
            
        for side in range(len(parts)):
            moments = cv2.moments(parts[side])
            if(moments['m00'] != 0):
                point = [moments['m01']/moments['m00']+x*side, y]
                res[side].append(point)
                if(output != None):
                    output[point[1]][point[0]] =  np.array([0,255,0], dtype=np.uint8)

    if(limit == None):
        return res[0]
    else:
        return res


def linearRegression(points, output=None):
    # this method make a linear regression with all points
    x,y = np.array(points).T
    param = np.linalg.lstsq(np.array([y, np.ones(y.shape)]).T, x)[0]
    line = np.array([param[0]*y+param[1],y]).T

    if(output != None):
        for x,y in line:
            output[y][x] = np.array([255,0,0], dtype=np.uint8)

    return line



def display(img, title):
    # this method display result (for demo)
    cv2.imshow(title, img)
    cv2.waitKey(0)



if(__name__ == "__main__"):
    img = substract(argv[1], argv[2])
    display(img, "Substraction result")

    img = filterNoise(img);
    display(img, "soft filter to delete noise")

    points = massCenter(img,img)
    display(img,"First mass center step")

    points = linearRegression(points, img)
    display(img, "linear regression result")

    res = np.zeros(img.shape, dtype=np.uint8)
    massCenter(img, res, points)
    display(res,"Second mass center step to fit lasers")

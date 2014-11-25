import cv2
import numpy as np
import matplotlib.pyplot as plt

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
    ret, img = cv2.threshold(img, 70, 255, cv2.THRESH_TOZERO)

    return img


def cutBetweenLasers(img, display=False, pixels=[]):
    # this method return the line which cut the picture between laser lines
    y = []
    x = []
    red = img[:,:,2]

    for line in range(img.shape[0]):
        moments = cv2.moments(red[line,:])
        if(moments['m00'] != 0):
            grav_x = moments['m01']/moments['m00']
            y.append(grav_x)
            x.append(line)

            if(display):
                img[line][np.round(grav_x)] = np.array([0,255,0], dtype=np.uint8)

    param = np.linalg.lstsq(np.array([x, np.ones(len(x))]).T, y)[0]
    between = np.array([x,param[0]*np.array(x)+param[1]]).T

    if(display):
        for line, limit in between:
            img[line][limit] = np.array([255,0,0], dtype=np.uint8)

    return img, between


def toLines(img, output, display=False):
    # this method try to find the mass center of each side of the picture
    img, between = cutBetweenLasers(img, display)

    for line, limit in between:
        offset = 0
        for side in (img[line,:limit,2],img[line,limit:,2]):
            moments = cv2.moments(side)
            if(moments['m00'] != 0):
                output[line][moments['m01']/moments['m00']+offset] = np.array([255,0,0], dtype=np.uint8)
            offset = limit

    return output


def plot(img):
    pass


if(__name__ == "__main__"):

    img = substract("./demo/vaselaser.jpg", "./demo/vase.jpg")
    img = filterNoise(img);
#   img = toLines(img, np.zeros(img.shape, dtype=np.uint8), True)
    img = toLines(img, img, True)
    plt.imshow(img)
    plt.show()

    plot(img);

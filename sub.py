import cv2
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

def subtract(a, b, threshold):
    res = np.empty_like(a)
    if (a.shape == b.shape):
        res[:] = a
        for x in range(len(a)):
            for y in range(len(a[0])):
                for z in range(len(a[0][0])):
                    if (z == 2):
                        aval = b[x][y][z]
                        bval = a[x][y][z]
                        if (aval > bval):
                            res[x][y][z] = aval-bval
                        elif (aval < bval):
                            res[x][y][z] = bval-aval
                        else:
                            res[x][y][z] = 0
                        if res[x][y][z] > threshold:
                            res[x][y][z] = 255
                        else:
                            res[x][y][z] = 0
                    else:
                        res[x][y][z] = 0
    return res

if __name__ == "__main__":

    vase = cv2.imread("demo/vase.jpg")
    vaselaser = cv2.imread("demo/vaselaser.jpg")

    resizeFactor = 0.5
    camdistance = 500.0
    middle = int(140*resizeFactor) # in pixels from the left edge

    res = subtract(vase, vaselaser, 100)
    res = cv2.resize(res, (0,0), fx=resizeFactor, fy=resizeFactor)
    #cv2.imshow('Vase', res)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()

    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_xlim3d(0,120)
    ax.set_ylim3d(0,120)
    ax.set_zlim3d(0,120)

    for y in range(len(res)):
        for x in range(0, middle):
            if (res[y][x][2] == 255):
                    a = camdistance/(-1+camdistance/(x-middle))
                    b = y
                    c = camdistance-(camdistance * a / (x-middle)) 
                    ax.scatter(int(a), int(b), int(c))
        for x in range(middle, len(res[0])):
            if (res[y][x][2] == 255):
                a = camdistance/(1+camdistance/(x-middle))
                b = y
                c = camdistance-(camdistance * a / (x-middle)) 
                ax.scatter(int(a), int(b), int(c))

    plt.show()

import time
import os
from math import sin,cos,tan,pi
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from cv2 import imread

from filter import*


def degToRad(degree):
    return (pi/180)*degree



def triangulation(points, L, H, k, gamma, alpha):
    res = []
    dy = L/(2*tan(alpha/2))

    for side in points:
        denom_const = dy/tan(gamma)
        for l,h in side:
            l = l -L/2
            h = H/2 -h

            rho = float(k)/(denom_const+l)

            res.append([rho*l, rho*dy, rho*h])

        k *= -1
        gamma = pi-gamma

    return res


def rotate(points, center, theta):

    for idx in range(len(points)):
        points[idx] = [points[idx][0]*cos(theta) + points[idx][1]*sin(theta) - center[1]*sin(theta),
                       -points[idx][0]*sin(theta) + points[idx][1]*cos(theta) + center[1]*(1-cos(theta)),
                       points[idx][2]]

    return points



def plot(points):
    points = np.array(points).T
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points[0], points[1], points[2], c='b', marker='.')
    plt.show()
    


if(__name__ == "__main__"):
    camera_center = 52
    angle_step = 11.5
    angle_laser = 100
    angle_camera = 60

    model = []

    files = os.listdir(argv[1])
    files.sort()
    files = files[:38]

    for idx in range(0,len(files),2):
        print("processing image %s & %s" %(files[idx], files[idx+1]))
        start = time.time()

        images = [imread(os.path.join(argv[1], files[i+1])) for i in range(2)]
        img = substract(*images)
        img = filterNoise(img)
        limit = linearRegression(massCenter(img))
        points = massCenter(img, limit)
        points = triangulation(points, img.shape[1], img.shape[0], camera_center/tan(degToRad(angle_laser)), degToRad(angle_laser), degToRad(angle_camera))
        model += rotate(points, (0,camera_center), idx*degToRad(angle_step))

        print("time : %.3f sec." %(time.time()-start))

    plot(model)

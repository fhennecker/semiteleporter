import time
import os
from math import sin,cos,tan,pi
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from filter import*


def degToRad(degree):
    return (pi/180)*degree



def triangulation(points, L, H, k, gamma, alpha):
    res = []
    L = float(L)
    H = float(H)
    k = float(k)
    dy = L/(2*tan(alpha/2))

    for side in points:
        denom_const = dy/tan(gamma)
        for l,h in side:
            l = l -L/2
            h = H/2 -h

            rho = k/(denom_const+l)

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
    model = []

    files = os.listdir(argv[1])
    files.sort()
    files = files[:38]

    for idx in range(0,len(files),2):
        print("processing image %s & %s" %(files[idx], files[idx+1]))
        start = time.time()

        img = substract(os.path.join(argv[1],files[idx]), os.path.join(argv[1],files[idx+1]))
        img = filterNoise(img)
        limit = linearRegression(massCenter(img))
        points = massCenter(img, limit)
        points = triangulation(points, img.shape[1], img.shape[0], 53/tan(degToRad(100)), degToRad(100), degToRad(60))
        model += rotate(points, (0,53), idx*degToRad(11.5))

        print("time : %.3f sec." %(time.time()-start))

    plot(model)

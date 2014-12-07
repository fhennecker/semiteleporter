import os
from math import sin,tan,pi
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

from filter import*


def degToRad(degree):
    return (pi/180)*degree



def triangulation(points, L, H, k, gamma, alpha):
    print(k)
    res = []
    dy = L/(2*tan(alpha/2))

    for side in points:
        denom_const = L/(2*tan(gamma)*tan(alpha/2))
        for l,h in side:
            l = l -L/2
            h = H/2 -h

            rho = k/(denom_const+l)

            res.append((rho*l, rho*dy, rho*h))

        k *= -1
        gamma *= -1

    return res



def plot(points):
    points = np.array(points).T
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points[0], points[1], points[2], c='b', marker='.')
    plt.show()
    


if(__name__ == "__main__"):
    points = []

    files = [argv[1], argv[2]]
    #files = os.listdir(argv[1])
    #files.sort()

    for idx in range(0,len(files),2):
        print("processing image %s & %s" %(files[idx], files[idx+1]))
        img = substract(os.path.join(argv[1],files[idx]), os.path.join(argv[1],files[idx+1]))
        img = filterNoise(img)
        limit = linearRegression(massCenter(img))
        points += massCenter(img, limit)

    points = triangulation(points, float(img.shape[1]), float(img.shape[0]), 53*tan(pi/2-degToRad(80)), degToRad(10), degToRad(60))
    plot(points)

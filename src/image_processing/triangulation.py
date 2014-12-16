import time
import os
from math import sin,cos,tan,atan,pi,radians,degrees
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from cv2 import imread
from multiprocessing import Pool

from filter import*



PLATFORM_RADIUS = 250.0                                # Radius of the plateform
CAMERA_POSITION = [0.0, 405.0, 50.0]                   # Position of the camera (by reference to the center of the plateform)
CAMERA_VISION   = radians(60)                          # Viewing angle of the camera
LASER_DIST      = 155.0                                # Distance between the laser and the camera
STEP_NUMBER     = 32                                   # Number of rotating steps

LASER_ANGLE     = atan(CAMERA_POSITION[1]/LASER_DIST)  # Orientation angle of the laser
STEP_ANGLE      = (2*pi)/STEP_NUMBER                   # Number of rotation steps




def triangulation(points, L, H, k, gamma, alpha):
    res = []
    dy = (L/2)/tan(alpha/2)
    denom_const = dy/tan(gamma)

    for l,h in points:
        l = l -L/2
        h = H/2 -h

        rho = k/(denom_const+l)
        point = [rho*l, rho*dy-CAMERA_POSITION[1], rho*h+CAMERA_POSITION[2]]

        if(point[2]>0 and (point[0]**2+point[1]**2)<PLATFORM_RADIUS**2):
            res.append(point)

    return res



def rotate(points, theta):

    for idx in range(len(points)):
        points[idx] = [points[idx][0]*cos(theta) - points[idx][1]*sin(theta), points[idx][0]*sin(theta) + points[idx][1]*cos(theta), points[idx][2]]

    return points



def step(directory, left_path, off_path, right_path, rotation):
    model = []

    print("processing image %s & %s & %s" %(left_path, off_path, right_path))

    left = cv2.imread(os.path.join(directory, left_path))
    off = cv2.imread(os.path.join(directory, off_path))
    right = cv2.imread(os.path.join(directory, right_path))

    # processing left laser
    img = substract(left, off)
    img = filterNoise(img)
    points = massCenter(img)
    points = triangulation(points, img.shape[1], img.shape[0], -LASER_DIST, pi-LASER_ANGLE, CAMERA_VISION)
    model += rotate(points, rotation)

    # processing right laser
    img = substract(right, off)
    img = filterNoise(img)
    points = massCenter(img)
    points = triangulation(points, img.shape[1], img.shape[0], LASER_DIST, LASER_ANGLE, CAMERA_VISION)
    model += rotate(points, rotation)

    return model



def plot(points):
    points = np.array(points).T
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.scatter(points[0], points[1], points[2], c='b', marker='.', s=2)
    ax.set_xlabel('X axis')
    ax.set_xlim3d(-100,100)
    ax.set_ylabel('Y axis')
    ax.set_ylim3d(-100,100)
    ax.set_zlabel('Z axis')
    ax.set_zlim3d(-10,190)
    plt.show()
    

def wrap_step(args):
    return step(*args)


if(__name__ == "__main__"):
    pictures  = os.listdir(argv[1])
    pictures.sort()
    pictures = pictures[:3*STEP_NUMBER]

    workers = None
    workers_args = [] 
    if(len(argv) > 2):
        workers = Pool(processes=argv[2])
    else:
        workers = Pool(processes=4)

    for idx in range(0,len(pictures),3):
        workers_args.append((argv[1], pictures[idx], pictures[idx+1], pictures[idx+2], STEP_ANGLE*(idx/3)))

    plot(sum(workers.map(wrap_step, workers_args), []))

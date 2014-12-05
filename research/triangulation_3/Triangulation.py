
# coding: utf-8

# In[1]:

import numpy as np
import matplotlib.pyplot as plt
from math import sin, cos, tan, atan, pi
from pylab import imread
from mpl_toolkits.mplot3d import Axes3D


# In[2]:

image = imread("lines1.png")
plt.imshow(image)
plt.show()


#### Formules de position

# In[3]:

def position(laser, gamma, theta, phi):
    """
    laser: position (x,y,z) du laser par rapport à la camera
    gamma: angle que fait le laser avec le plan ortogonal à la caméra
    theta: angle horizontal du rayon de la camera
    phi  : angle vertical du rayon de la camera
    """
    # vecteur directeur du rayon sortant de la camera
    ray = np.array([sin(theta), cos(theta), tan(phi)])
    
    # Matrice tq (matrix) * (l, m, z) = (laser)
    matrix = np.array([
        [cos(gamma), 0, sin(theta)],
        [sin(gamma), 0, cos(theta)],
        [         0, 1, tan(phi)  ]
    ])
    l, m, z = np.linalg.solve(matrix, -laser)
    return z * ray


# In[4]:

CAMERA_HEIGHT = 39
PLATE_HEIGHT  = 18.5
RELATIVE_HEIGHT = CAMERA_HEIGHT - PLATE_HEIGHT
CAM_DISTANCE = 53.2

def theta_phi(alpha, image_shape, position):
    x, y = map(float, position)
    w, h = map(float, image_shape)
    ratio = w/h
    beta = alpha / ratio
    theta = (x - w/2)/w * alpha
    phi = (h/2 - y)/h * beta
    return theta, phi


#### Paramètres du sytème

# In[5]:

def deg2rad(x): return pi*float(x)/180
def rad2deg(x): return 180*float(x)/pi

GAMMA_D = deg2rad(83)
GAMMA_G = deg2rad(78)
ALPHA = deg2rad(60)
LASER_G = np.array([CAM_DISTANCE * tan(pi/2-GAMMA_G), 0, 0])
LASER_D = np.array([CAM_DISTANCE * tan(pi/2-GAMMA_D), 0, 0])


# In[6]:

tuple(position(LASER_G, GAMMA_G, 0, 0)) # Devrait être (0, 53.2, 0)


#### Calcul des positions des points

# In[7]:

XYZ = []
IJ = []
H, W = image.shape[:2]
for i in range(H):
    for j in range(W):
        if tuple(image[i][j]) != (0, 0, 0):
            IJ.append((j, i))
            theta, phi = theta_phi(ALPHA/2, [W, H], [j, i])
            gamma = GAMMA_G if theta < 0 else GAMMA_D
            laser = LASER_G if theta < 0 else LASER_D
            XYZ.append(position(laser, gamma, theta, phi))

X, Y, Z = map(np.array, zip(*XYZ))
I, J = map(np.array, zip(*IJ))
XYZ[0]


# In[8]:

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X, Y, Z)
ax.plot([0, 0], [0, CAM_DISTANCE], [0, 0], color='red')
plt.xlim(-50, 50)
plt.ylim(0, 60)
plt.show()


# In[9]:

photo = imread("imgs/04.png")
h, w = photo.shape[:2]
plt.imshow(photo)
plt.scatter(I, J)
plt.plot([w/2, w/2], [0, h], 'y')
plt.show()


# In[10]:

get_ipython().magic(u'pinfo plt.grid')


# In[10]:




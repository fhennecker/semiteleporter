# -*- coding: utf-8 -*-

import numpy as np
import cv2
from pylab import imread
from math import sin, cos, tan, atan, asin, pi, hypot
import json
from filter import findPoints, filterNoise, substract
from multiprocessing import Pool
import traceback

def deg2rad(x): return pi*float(x)/180
def rad2deg(x): return 180*float(x)/pi

# Mesures
R = 250.0   # Rayon du plateau
L = 405.0   # Distance de la camera au centre du plateau (mm)
H_C = 240.0 # Hauteur de la camera (mm)
H_P = 185.0 # Hauteur du plateau (mm)

GAMMA_D = -atan(L/155) # Angle entre le laser gauche et le plan de l'image
GAMMA_G = atan(L/155)  # Angle entre le laser droit et le plan de l'image
ALPHA = deg2rad(60)    # Angle d'ouverture horizontal de la camera

# Calibration: centre du plateau sur l'image (en pixels)
CX, CY = 943, 743

# Deductions
H_RELATIVE = H_C - H_P # Hauteur relative de la camera par rapport au plateau
DELTA = asin(H_RELATIVE/L) # Angle de plongée de la caméra
CAM = np.array([0, -L, H_RELATIVE]) # Position de la camera


def position(gamma, theta, phi):
    """
    Renvoie la position du point à l'intersection
    - Du laser qui forme un angle gamma avec le plan de l'image
    - Du rayon de la camera
      - d'angle horizontal theta (gauche < 0 < droit)
      - d'angle vertical phi (bas < 0 < haut)
    Renvoie un point (np.array)
    """
    # vecteur directeur du rayon sortant de la camera
    ray = np.array([sin(theta), cos(theta), sin(phi-DELTA)])
    laser = np.array([L * tan(pi/2 - gamma), 0, 0])
    
    # Matrice tq (matrix) * (l, m, z) = (laser)
    matrix = np.array([
        [cos(gamma), 0, sin(theta)],
        [sin(gamma), 0, cos(theta)],
        [         0, 1, sin(phi-DELTA)]
    ])
    l, m, z = np.linalg.solve(matrix, -laser)
    return CAM + z * ray


def theta_phi(alpha, image_shape, position):
    """
    Renvoie la paire d'angle (horizontal, vertical) qu'a le rayon sortant de la
    camera, à la position donnée (en pixel), par rapport à la forme de l'image
    (en pixels), et l'angle d'ouverture horizontal de la camera (alpha)
    Renvoie un tuple d'angles en radians
    """
    x, y = map(float, position)
    w, h = map(float, image_shape)
    ratio = w/h
    beta = alpha / ratio
    theta = (x - CX)/(w/2) * alpha
    phi = (CY - y)/(h/2) * beta
    return theta, phi


def reduce_pointset(points, thres=0.1):
    """
    Apply Douglas-Peucker algorithm on a laser plane defined point set to 
    reduce the number of points
    """
    # On ordonne les points verticalement
    points.sort(key=lambda x: x[2])
    return points

def extract_points(with_lasers_path, without_lasers_path, rotation, gamma):
    """
    Extrait les points en 3D d'une paire d'images (avec et sans lasers).
    On passe le chemin des images, et l'angle de rotation du plateau. 
    Renvoie une liste de np.arrays (les points en 3D)
    """
    res = []
    try:
        laser, off = cv2.imread(with_lasers_path), cv2.imread(without_lasers_path)
        H, W = laser.shape[:2]
        # Matrice de rotation (x,y tournent autour du centre du plateau, z inchangé)
        ROTMATRIX = np.array([
            [ cos(rotation), sin(rotation), 0], 
            [-sin(rotation), cos(rotation), 0], 
            [             0,             0, 1]
        ])
        for j, i in findPoints(laser, off):
            theta, phi = theta_phi(ALPHA, [W, H], [j, i])
            pos = position(gamma, theta, phi).dot(ROTMATRIX)

            x, y, z = pos
            # Ignore les points en dehors du plateau
            if z > 0 and x*x + y*y < R*R:
                res.append(pos)
        print "\033[32mDone with %s-%s\033[0m" % (with_lasers_path, without_lasers_path)
    except:
        print "\033[31mError with %s-%s" % (with_lasers_path, without_lasers_path)
        traceback.print_exc()
        print "\033[0m"
    return reduce_pointset(res)


def wrap_extract_points(args):
    """"""
    return extract_points(*args)


def build_3d(first_img_num=0, last_img_num=32, n_workers=8):
    """
    Construit un modèle 3D a partir des images (hardcode pour le moment).
    Utilise n_workers threads pour faire les calculs en parallèle
    """
    workers = Pool(processes=n_workers)
    workers_args = [
        (
            "imgs/%02d-left.png"%(i), 
            "imgs/%02d-off.png"%(i), 
            i*pi/16,
            GAMMA_G
        ) 
    for i in range(first_img_num, last_img_num)]
    workers_args += [
        (
            "imgs/%02d-right.png"%(i), 
            "imgs/%02d-off.png"%(i), 
            i*pi/16,
            GAMMA_D
        ) 
    for i in range(first_img_num, last_img_num)]

    # Unpack des arguments pour extract_points
    XYZ = sum(workers.map(wrap_extract_points, workers_args), [])
    return XYZ


# ## Et oui, on aime les graphiques !
if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    XYZ = build_3d(n_workers=8)

    fig = plt.figure()
    R = 250
    disk = [(x, y, 0) for x in np.linspace(-R, R) for y in np.linspace(-R, R) if hypot(x, y) <= R]
    ax = fig.add_subplot(111, projection='3d', aspect="equal")
    X, Y, Z = zip(*XYZ)
    ax.scatter(X, Y, Z, '.', s=2)
    diskX, diskY, diskZ = zip(*disk)
    ax.plot(diskX, diskY, diskZ, '.', color='g', alpha=0.25)
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_zlim(-R, R)
    plt.show()

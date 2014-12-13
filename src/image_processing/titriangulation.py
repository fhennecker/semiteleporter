# -*- coding: utf-8 -*-

import numpy as np
import cv2
from math import sin, cos, tan, atan, asin, pi, hypot
import json
from filter import findPoints
from douglaspeucker import reduce_pointset
import traceback

def deg2rad(x): return pi*float(x)/180
def rad2deg(x): return 180*float(x)/pi

def triangulation(L, H, CX, CY, GAMMA, imageW=1920, imageH=1080):
    # Mesures
    R = 250.0              # Rayon du plateau
    ALPHA = deg2rad(72)    # Angle d'ouverture horizontal de la camera

    # Deductions
    DELTA = asin(H/L) # Angle de plongée de la caméra
    CAM = np.array([0, -L, H]) # Position de la camera
    LASER = np.array([L * tan(pi/2 - GAMMA), 0, 0]) #Vecteur directeur du laser
    ASPECT = imageW/imageH # Aspect de l'image
    BETA = 0.5 * ALPHA / ASPECT  # Angle d'ouverture vertical de la camera

    # Precalcul de cos(GAMMA) et sin(GAMMA)
    cosG, sinG = cos(GAMMA), sin(GAMMA)

    def position(theta, phi):
        # vecteur directeur du rayon sortant de la camera
        ray = np.array([sin(theta), cos(theta), sin(phi-DELTA)])
        # Matrice tq (matrix) * (l, m, z) = (laser)
        matrix = np.array([
            [cosG, 0, ray[0]],
            [sinG, 0, ray[1]],
            [   0, 1, ray[2]]
        ])
        l, m, z = np.linalg.solve(matrix, -LASER)
        return CAM + z * ray

    def theta_phi(x, y):
        theta = ALPHA * float(x - CX)/(imageW/2)
        phi = BETA * float(CY - y)/(imageH/2)
        return theta, phi

    def extract_points(rotation, points):
        res = []
        rotation *= -1
        # Matrice de rotation (x,y tournent autour du centre du plateau, z inchangé)
        ROTMATRIX = np.array([
            [ cos(rotation), sin(rotation), 0], 
            [-sin(rotation), cos(rotation), 0], 
            [             0,             0, 1]
        ])
        for j, i in points:
            theta, phi = theta_phi(j, i)
            pos = position(theta, phi).dot(ROTMATRIX)

            x, y, z = pos
            # Ignore les points en dehors du plateau
            if hypot(x, y) < R:
                res.append(pos)
        return res

    return extract_points

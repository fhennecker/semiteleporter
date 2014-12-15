"""
Main script for the 3D scanner
"""

from renderer import Renderer, RenderParams
from scanner import Scanner
from filter import findPoints
from titriangulation import triangulation
from douglaspeucker import reduce_pointset
from math import atan, pi, hypot
import argparse
import json
import sys

def img2points(angle, *args):
    """Convert a pair of images to detected laser points"""
    return angle, findPoints(*args)

def curried_reduce_pointset(thres):
    """Curry reduce_pointset with given threshold"""
    def wrap(points):
        return reduce_pointset(points, thres)
    return wrap

def plot3D(**points_series):
    import matplotlib.pyplot as plt
    from mpl_toolkits.mplot3d import Axes3D
    import numpy as np
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d', aspect="equal")
    for color, points in points_series.iteritems():
        if len(points) > 0:
            X, Y, Z = zip(*points)
            ax.plot(X, Y, Z, '.', color=color, alpha=0.25)

    R = 250
    disk = [(x, y, 0) for x in np.linspace(-R, R) for y in np.linspace(-R, R) if hypot(x, y) <= R]
    diskX, diskY, diskZ = zip(*disk)
    ax.plot(diskX, diskY, diskZ, '.', color='g', alpha=0.25)

    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_zlim(-R, R)
    plt.show()

def main(OPTIONS, prompt=raw_input):
    """
    Main glue function. Return an iterator on (progress, text), where
    - progress is a float between 0 and 1 indicating global reconstruction progress
    - text is the description of the current phase
    The parameter prompt is a function that prompts for user input (takes a
    text as param, return user input)
    """
    LASER_LEFT = 155.0 # Decalage du laser gauche en mm
    LASER_RIGHT  = 175.0 # Decalage du laser droit en mm
    OPTIONS.n_frames = min(OPTIONS.n_frames, 80)

    scanner = Scanner(arduino_dev=OPTIONS.serial_port, cam_id=OPTIONS.cam_index)
    imgsrc = scanner.replay(OPTIONS.dump_dir, OPTIONS.n_frames) if OPTIONS.dump_dir else scanner.scan(OPTIONS.dest_dir, OPTIONS.n_frames)

    if not OPTIONS.dump_dir:
        prompt("Calibration. Assurez vous que le plateau est vide")
        scanner.calibrate(OPTIONS.dest_dir)
        prompt("Calibration finie. Placez l'objet")
    
    yield 0, "Start scanning"
    params = RenderParams(
        CX=OPTIONS.cx, CY=OPTIONS.cy, THRES=OPTIONS.reduce_thres,
        L=OPTIONS.L, LASER_L=LASER_LEFT, LASER_R=LASER_RIGHT
    )

    i = 0
    all_points = []
    for points in Renderer(params, imgsrc):
        all_points += points
        progress = float(i)/(2*OPTIONS.n_frames)
        yield progress, "Scanning (%d points)..." % (len(all_points))
        i += 1

    if OPTIONS.json:
        json.dump(map(list, all_points), open(OPTIONS.json, 'w'))
    yield 1, "Have %d points" % (len(all_points))
    if OPTIONS.show_scene:
        plot3D(black=all_points)

optparser = argparse.ArgumentParser(
    description="The 3D scanner main program"
)
optparser.add_argument(
    '-p', '--port', type=str,
    action='store', dest='serial_port', default="/dev/ttyACM0",
    help="Serial port for arduino"
)
optparser.add_argument(
    '-c', '--camera-index', type=int,
    action='store', dest='cam_index', default=0,
    help="Camera index (Video4Linux)"
)
optparser.add_argument(
    '-D', '--use-dump', type=str,
    action='store', dest='dump_dir', default=None,
    help="Use dumped images instead of camera"
)
optparser.add_argument(
    '-d', '--dump', type=str,
    action='store', dest='dest_dir', default=None,
    help="Dump camera images to this directory"
)
optparser.add_argument(
    '-t', '--threshold', type=float,
    action='store', dest='reduce_thres', default=1,
    help="Threshold for point reduction algorithm"
)
optparser.add_argument(
    '-X', '--center-x', type=int,
    action='store', dest='cx', default=960,
    help="Center of plate on the captured image, in pixels"
)
optparser.add_argument(
    '-Y', '--center-y', type=int,
    action='store', dest='cy', default=540,
    help="Center of plate on the captured image, in pixels"
)
optparser.add_argument(
    '-L', '--length', type=float,
    action='store', dest='L', default=375,
    help="Distance in mm from the center of the plate to the camera"
)
optparser.add_argument(
    '-n', '--n-frames', type=int,
    action='store', dest='n_frames', default=80,
    help="Number of frames to take (will only take the n firsts on 80)"
)
optparser.add_argument(
    '-j', '--json', type=str,
    action='store', dest='json', default=None,
    help="Output points as a json list to this file"
)
optparser.add_argument(
    '-H', '--hide',
    action='store_false', dest='show_scene', default=True,
    help="Do not show resulting pointcloud with Matplotlib"
)

if __name__ == '__main__':
    def progress_bar(progress, width=25):
        n = int(round(width*progress))
        return "\033[43m%s\033[0;33m%s %d%%\033[0m" % (n*' ', (width-n)*'-', 100*progress)

    for progress, text in main(optparser.parse_args()):
        text = "\r%s %s" % (progress_bar(progress), text)
        sys.stdout.write(text.rjust(80))
        sys.stdout.flush()
    print


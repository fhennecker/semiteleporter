from pipeline import Pipeline
from scanner import Scanner
from filter import findPoints
from titriangulation import triangulation
from douglaspeucker import reduce_pointset
from math import atan, pi, hypot
import argparse
import json

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
            ax.scatter(X, Y, Z, color=color, alpha=0.25)

    R = 250
    disk = [(x, y, 0) for x in np.linspace(-R, R) for y in np.linspace(-R, R) if hypot(x, y) <= R]
    diskX, diskY, diskZ = zip(*disk)
    ax.plot(diskX, diskY, diskZ, '.', color='g', alpha=0.25)

    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)
    ax.set_zlim(-R, R)
    plt.show()

def main(OPTIONS):
    print "RUNNING PROGRAM WITH OPTIONS", OPTIONS
    GAMMA_G = atan(OPTIONS.L/155)  # Angle entre le laser gauche et le plan de l'image
    GAMMA_D = -atan(OPTIONS.L/155) # Angle entre le laser droit et le plan de l'image
    left_pipe = Pipeline(
        img2points,
        triangulation(OPTIONS.L, 55.0, OPTIONS.cx, OPTIONS.cy, GAMMA_G),
        curried_reduce_pointset(OPTIONS.reduce_thres)
    )
    right_pipe = Pipeline(
        img2points,
        triangulation(OPTIONS.L, 55.0, OPTIONS.cx, OPTIONS.cy, GAMMA_D),
        curried_reduce_pointset(OPTIONS.reduce_thres)
    )

    OPTIONS.n_frames = min(OPTIONS.n_frames, 80)

    scanner = Scanner(arduino_dev=OPTIONS.serial_port, cam_id=OPTIONS.cam_index)
    imgsrc = scanner.replay(OPTIONS.dump_dir, OPTIONS.n_frames) if OPTIONS.dump_dir else scanner.scan(OPTIONS.dest_dir, OPTIONS.n_frames)

    if not OPTIONS.dump_dir:
        raw_input("Calibration. Assurez vous que le plateau est vide, puis enter")
        scanner.calibrate(OPTIONS.dest_dir)
        raw_input("Calibration finie. Placez l'objet, puis enter")
    
    left_points, right_points = [], []
    with left_pipe, right_pipe:
        img_count = 0
        for angle, off, left, right in imgsrc:
            if not OPTIONS.right_only:
                left_pipe.feed(angle, left, off)
            if not OPTIONS.left_only:
                right_pipe.feed(angle, right, off)
            print "Acquired images at %d deg" % (180*angle/pi)
            img_count += 1

        for i in range(img_count):
            if not OPTIONS.right_only:
                left_points += left_pipe.retire()
            if not OPTIONS.left_only:
                right_points += right_pipe.retire()
            print "Images %d done" % (i+1)

    all_points = left_points + right_points
    if OPTIONS.json:
        json.dump(map(list, all_points), open(OPTIONS.json, 'w'))
    print "Have %d points" % (len(all_points))
    plot3D(b=left_points, r=right_points)


if __name__ == '__main__':
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
        '-l', '--left-only',
        action='store_true', dest='left_only', default=False,
        help="Use only left laser"
    )
    optparser.add_argument(
        '-r', '--right-only',
        action='store_true', dest='right_only', default=False,
        help="Use only right laser"
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
        help="Number of frames to take (will only take the n firsts on 80"
    )
    optparser.add_argument(
        '-j', '--json', type=str,
        action='store', dest='json', default=None,
        help="Output points as a json list to this file"
    )
    main(optparser.parse_args())


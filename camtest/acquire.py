import cv2
from time import time
from serial import Serial
from sys import stdout
from time import sleep
import traceback

CV_CAP_PROP_FRAME_WIDTH  = 3
CV_CAP_PROP_FRAME_HEIGHT = 4
CV_CAP_PROP_FRAME_COUNT = 7


with Serial("/dev/ttyACM0", 9600) as arduino:
    def command(cmd):
        start = time()
        arduino.write(cmd)
        while arduino.read(1) != cmd:
            pass
        print "TEMPS:", time()-start

    def photo(command_before, name=None):
        if name:
            print name
        command(command_before)
        capture = cv2.VideoCapture(0)
        capture.set(CV_CAP_PROP_FRAME_WIDTH, 1920)
        capture.set(CV_CAP_PROP_FRAME_HEIGHT, 1080)
        ok, img = capture.read()
        capture.release()
        if not ok:
            raise Exception("Unable to read image after command %s" % (command_before))
        if name:
            print "/%s" % (name)
        return img

    def triphoto():
        return map(photo, [('l', 'Left laser'), ('0', 'No laser'), ('r', 'Right laser')])

    i = 0
    while True:
        raw_input("Photo ? ")
        off, left, right = triphoto()
        cv2.imwrite("imgs/%02d-off.png" % (i), off)
        cv2.imwrite("imgs/%02d-left.png" % (i), left)
        cv2.imwrite("imgs/%02d-right.png" % (i), right)
        i += 1

import cv2
import os
from serial import Serial
from math import pi
from time import sleep
from filter import calibrationMask

class Scanner:
    """
    Hardware control class
    """
    CV_CAP_PROP_FRAME_WIDTH  = 3
    CV_CAP_PROP_FRAME_HEIGHT = 4

    class CaptureError(Exception):
        pass

    def __init__(self, arduino_dev="/dev/ttyACM0", cam_id=0):
        self.arduino_dev = arduino_dev
        self.cam_id = cam_id
        self.W, self.H = 1920, 1080

    def command_arduino(self, cmd):
        """
        Send a command to the arduino and wait for its answer
        """
        assert len(cmd) == 1
        self.arduino.write(cmd)
        while self.arduino.read(1) != cmd:
            pass

    def photo(self):
        """
        Capture an image from the camera
        """
        capture = cv2.VideoCapture(self.cam_id)
        capture.set(self.CV_CAP_PROP_FRAME_WIDTH, self.W)
        capture.set(self.CV_CAP_PROP_FRAME_HEIGHT, self.H)
        ok, img = capture.read()
        capture.release()
        if not ok:
            raise self.CaptureError()
        return img

    def photo_filename(self, dir, idx, suffix):
        return os.path.join(dir, "%02d-%s.png"%(idx, suffix))

    def wait_arduino_boot(self):
        sleep(3)

    def scan(self, dump_to_dir=None):
        """
        Return an iterator on (A, Io, Il, Ir), where
        - A is the current angle
        - Io is the image without lasers
        - Il is the image with left laser
        - Ir is the image with right laser

        If dump_to_dir is a non-empty string, save copy of taken images to this
        directory.
        """
        with Serial(self.arduino_dev, 9600) as self.arduino:
            self.wait_arduino_boot() # Wait arduino boot
            self.command_arduino('0') # Shut off lasers
            for i in range(80):
                off = self.photo()
                self.command_arduino('l') # Left laser on
                left = self.photo()
                self.command_arduino('r') # Right laser on
                right = self.photo()
                self.command_arduino('0') # Shut off lasers
                self.command_arduino('t') # Turn
                angle = 2*pi*i/80
                if dump_to_dir is not None:
                    cv2.imwrite(self.photo_filename(dump_to_dir, i, 'off'), off)
                    cv2.imwrite(self.photo_filename(dump_to_dir, i, 'left'), left)
                    cv2.imwrite(self.photo_filename(dump_to_dir, i, 'right'), right)
                left  *= self.mask
                right *= self.mask
                yield angle, off, left, right

    def replay(self, from_dir, n_angles=80):
        """
        Return an iterator on (A, Io, Il, Ir), where
        - A is the current angle
        - Io is the image without lasers
        - Il is the image with left laser
        - Ir is the image with right laser
        """
        self.mask = cv2.imread(os.path.join(from_dir, "calibration.png"))
        for i in range(n_angles):
            off   = cv2.imread(self.photo_filename(from_dir, i, 'off'))
            left  = cv2.imread(self.photo_filename(from_dir, i, 'left'))
            right = cv2.imread(self.photo_filename(from_dir, i, 'right'))
            angle = 2*pi*i/80
            left  *= self.mask
            right *= self.mask
            yield angle, off, left, right

    def calibrate(self, dump_to_dir=None):
        with Serial(self.arduino_dev, 9600) as self.arduino:
            self.wait_arduino_boot()
            self.command_arduino('b')
            img_with = self.photo()
            self.command_arduino('0')
            img_without = self.photo()
            self.mask = calibrationMask(img_with, img_without)
            if dump_to_dir is not None:
                cv2.imwrite(os.path.join(dump_to_dir, "calibration.png"), self.mask)

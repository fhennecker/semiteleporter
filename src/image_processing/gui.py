import Tkinter as tk
import cv2
import numpy as np
from PIL import Image, ImageTk
from scanner import Scanner

def vertical_separator(parent, width):
    return tk.Frame(parent, height=3, width=width, bd=1, relief=tk.SUNKEN)

def horizontal_separator(parent, height):
    return tk.Frame(parent, height=height, width=3, bd=1, relief=tk.SUNKEN)

class ButtonBar(tk.Frame):
    def __init__(self, parent, app, width, height, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        self.app = app
        self.build_scanner_input_menus(width, height)
        self.build_action_buttons(width, height)

    def refresh_scanner_input_menus(self):
        self.arduino_menu.option_clear()
        for option in Scanner.list_arduinos_candidates():
            self.arduino_menu.option_add(option, option)
        self.camera_menu.option_clear()
        for option in Scanner.list_cameras_indexes():
            self.camera_menu.option_add(str(option), str(option))

    def build_scanner_input_menus(self, w, h):
        tk.Button(self, text="Detect", command=self.refresh_scanner_input_menus).pack()

        tk.Label(self, text="Arduino serial port").pack()
        self.arduino = tk.StringVar(self)
        self.arduino.set(self.app.scanner.arduino_dev)
        options = Scanner.list_arduinos_candidates()
        self.arduino_menu = tk.OptionMenu(self, self.arduino, *options)
        self.arduino_menu.pack()
        
        tk.Label(self, text="Camera number").pack()
        self.camera = tk.StringVar(self)
        self.camera.set(str(self.app.scanner.cam_id))
        options = Scanner.list_cameras_indexes()
        self.camera_menu = tk.OptionMenu(self, self.camera, *options)
        self.camera_menu.pack()
        
        vertical_separator(self, w).pack()

    def build_action_buttons(self, w, h):
        tk.Button(self, text="Calibration", command=self.app.calibrate).pack()
        tk.Button(self, text="Scan", command=self.app.scan).pack()
        vertical_separator(self, w).pack()

class ImageZone(tk.Frame):
    def __init__(self, parent, app, width, height, **kwargs):
        tk.Frame.__init__(self, parent, width=width, height=height, **kwargs)
        self.W, self.H = width, height
        self.imglabel = tk.Label(self)
        self.show_image(255*np.ones((height, width)))
        self.imglabel.pack()

    def show_image(self, image):
        if tuple(image.shape[:2]) != (self.H, self.W):
            image = cv2.resize(image, (self.W, self.H), interpolation=cv2.INTER_AREA)
        self.imgtk = ImageTk.PhotoImage(image=Image.fromarray(image))
        self.imglabel.configure(image=self.imgtk)

class InfoBar(tk.Frame):
    def __init__(self, parent, app, **kwargs):
        tk.Frame.__init__(self, parent, **kwargs)
        tk.Label(self, text="Semiteleporter, the 3D Scanner. Quit with ctrl-q or ctrl-w").pack()

class MainFrame(tk.Frame):
    def __init__(self, app, **kwargs):
        iH = 500 # Image height
        iW = int(iH*app.scanner.aspect()) # Image width
        bW, bH = 200, 100 # Bars width and height
        W, H = iW + bW, iH + bH
        tk.Frame.__init__(self, app, width=W, height=H, **kwargs)
        self.pack(fill=tk.BOTH)
        self.infobar = InfoBar(self, app, width=W, height=bH)
        self.infobar.pack()
        self.imgzone = ImageZone(self, app, width=iW, height=iH)
        self.imgzone.pack(side="left")
        self.butbar = ButtonBar(self, app, width=bW, height=iH)
        self.butbar.pack(side="right")

class App(tk.Tk):
    def __init__(self, scanner):
        tk.Tk.__init__(self)
        self.scanner = scanner
        self.bind('<Control-q>', lambda ev: self.quit())
        self.bind('<Control-w>', lambda ev: self.quit())
        self.arduino = tk.StringVar(self)
        self.arduino.set(scanner.arduino_dev)
        self.camera = tk.StringVar(self)
        self.camera.set(str(scanner.cam_id))
        self.frame = MainFrame(self)

    def calibrate(self):
        self.scanner.arduino_dev = self.arduino.get()
        self.scanner.cam_id = int(self.camera.get())
        mask = self.scanner.calibrate()
        self.frame.imgzone.show_image((255*mask).clip(0, 255))

    def scan(self):
        print "Scan !"

if __name__ == "__main__":
    gui = App(Scanner())
    gui.mainloop()
    gui.destroy()

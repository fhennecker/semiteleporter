#!/usr/bin/env python

import Tkinter as tk
import cv2
import numpy as np
import tkMessageBox, tkFileDialog
from PIL import Image, ImageTk
from scanner import Scanner
from renderer import RenderParams, Renderer
from filter import findCenter
from math import hypot
from os import path
from ObjConverter import ObjConverter

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Shortcuts
def IntVar(master, value=0): 
    res = tk.IntVar(master)
    res.set(value)
    return res

def DoubleVar(master, value=0): 
    res = tk.DoubleVar(master)
    res.set(value)
    return res

def StringVar(master, value=""):
    res = tk.StringVar(master)
    res.set(value)
    return res

def BooleanVar(master, value=False):
    res = tk.BooleanVar(master)
    res.set(value)
    return res

def vertical_separator(parent, width):
    return tk.Frame(parent, height=3, width=width, bd=1, relief=tk.SUNKEN)

class ButtonBar(tk.Frame):
    """Action button bar on the left side"""
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
        tk.Button(self, text="Scan", command=self.app.scan).pack()
        tk.Button(self, text="Scan & Dump", command=self.app.scan_dump).pack()
        tk.Button(self, text="Open dump", command=self.app.open).pack()
        vertical_separator(self, w).pack()
        tk.Button(self, text="Export .obj", command=self.app.export_obj).pack()
        vertical_separator(self, w).pack()

class ImageZone(tk.Frame):
    """Main image zone"""
    class Mode2D:
        pass

    class Mode3D:
        pass

    def __init__(self, parent, app, width, height, **kwargs):
        tk.Frame.__init__(self, parent, width=width, height=height, **kwargs)
        self.app = app
        self.W, self.H = width, height
        self.fig = plt.figure()

        # Add to canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.show()
        self.canvas.get_tk_widget().pack()
        self.show_image(0x33*np.ones((height, width, 3), dtype=np.uint8))
        self.canvas.mpl_connect('button_press_event', self)
        app.Cx.trace('w', self.update_cross)
        app.Cy.trace('w', self.update_cross)

    def __call__(self, event):
        """Callback for matplotlib events"""
        x, y = event.xdata, event.ydata
        if x is None or y is None or self.mode is self.Mode3D:
            return
        self.app.Cx.set(x/self.W)
        self.app.Cy.set(y/self.H)
        self.show_cross()
        self.app.is_calibrated.set(True)

    def show_image(self, image):
        self.fig.clear()
        self.mode = self.Mode2D
        if tuple(image.shape[:2]) != (self.H, self.W):
            image = cv2.resize(image, (self.W, self.H), interpolation=cv2.INTER_AREA)
        self.image = image
        ax = self.fig.add_subplot(111)
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
        ax.axis('off')
        ax.imshow(self.image)
        self.canvas.draw()
        return ax

    def show_cross(self):
        x = self.W * self.app.Cx.get()
        y = self.H * self.app.Cy.get()
        ax = self.show_image(self.image)
        ax.plot([x, x], [0, self.H], 'r', zorder=1)
        ax.plot([0, self.W], [y, y], 'r', zorder=2)
        self.canvas.draw()

    def update_cross(self, *args):
        if self.mode == self.Mode2D:
            self.show_cross()

    def add_3D_points(self, ax, points):
        assert self.mode == self.Mode3D
        if len(points) > 0:
            X, Y, Z = zip(*points)
            ax.plot(X, Y, Z, '.', color='black', alpha=0.25)
            self.canvas.draw()
        return ax

    def show_3D(self, points):
        self.fig.clear()
        self.mode = self.Mode3D

        # Draw points
        ax = self.fig.add_subplot(111, projection='3d', aspect="equal")
        ax.axis('off')
        plt.subplots_adjust(left=0, right=1, top=1, bottom=0)

        # Draw plate in green
        R = 250
        disk = [(x, y, 0) for x in np.linspace(-R, R) for y in np.linspace(-R, R) if hypot(x, y) <= R]
        diskX, diskY, diskZ = zip(*disk)
        ax.plot(diskX, diskY, diskZ, '.', color='g', alpha=0.25)
        ax.set_xlim(-R, R)
        ax.set_ylim(-R, R)
        ax.set_zlim(0, 2*R)
        self.add_3D_points(ax, points)
        return ax

class InfoBar(tk.Frame):
    """Information and parameters bar"""
    def __init__(self, parent, app, **kwargs):
        infos = (
            (("Cam lens <-> plate center (mm)", app.L), ("Relative cam height (mm)", app.H)), 
            (("Center x (ratio)", app.Cx), ("Center y (ratio)", app.Cy)),
            (("Left laser relative x (mm)", app.LASER_L), ("Right laser relative x (mm)", app.LASER_R))
        )
        tk.Frame.__init__(self, parent, **kwargs)
        tk.Label(self, textvariable=app.infotext).pack()
        tk.Label(self, text="Calibrated:").pack(side="left")
        tk.Label(self, textvariable=app.is_calibrated).pack(side="left")

        frame = tk.Frame(self)
        row = 0
        for line in infos:
            col = 0
            for name, var in line:
                tk.Label(frame, text=name).grid(row=row, column=col)
                tk.Entry(frame, textvariable=var).grid(row=row, column=col+1)
                col += 2
            row += 1
        tk.Label(frame, text="Minimum significant line deviation").grid(row=row, column=0)
        tk.Scale(frame, from_=0, to=5, variable=app.THRES, resolution=0.1, orient=tk.HORIZONTAL).grid(row=row, column=1)
        tk.Button(frame, text="Save params", command=app.save_config).grid(row=row, column=2)
        tk.Button(frame, text="Load params", command=app.load_config).grid(row=row, column=3)
        frame.pack()

class MainFrame(tk.Frame):
    """Main GUI frame"""
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
    DESCRIPTION = "Semiteleporter, the 3D Scanner. Quit with ctrl-q or ctrl-w"

    def __init__(self, scanner):
        tk.Tk.__init__(self)
        self.scanner = scanner
        self.bind('<Control-q>', lambda ev: self.quit())
        self.bind('<Control-w>', lambda ev: self.quit())

        self.infotext = StringVar(self, self.DESCRIPTION)

        # Configuration variables
        self.arduino = StringVar(self, scanner.arduino_dev)
        self.camera = StringVar(self, str(scanner.cam_id))
        self.is_calibrated = BooleanVar(self, False)
        
        # Calibration
        self.Cx = DoubleVar(self, 0.5)
        self.Cy = DoubleVar(self, 0.5)
        self.L = DoubleVar(self, 355)
        self.H = DoubleVar(self, 55)
        self.LASER_L = DoubleVar(self, -155)
        self.LASER_R = DoubleVar(self, 155)
        self.THRES = DoubleVar(self, 1)

        # Results
        self.points = None

        # Build GUI
        self.frame = MainFrame(self)

    @property
    def render_params(self):
        return RenderParams(
            CX=self.Cx.get()*self.scanner.W,
            CY=self.Cy.get()*self.scanner.H,
            H=self.H.get(),
            L=self.L.get(),
            LASER_L=self.LASER_L.get(),
            LASER_R=self.LASER_R.get(),
            THRES=self.THRES.get()
        )

    def do_scan(self):
        self.infotext.set("Scanning...")
        all_points = []
        ax = self.frame.imgzone.show_3D(all_points)
        for points in Renderer(self.render_params, self.scan_iter):
            all_points += points
            self.infotext.set("Have %d points..." % len(all_points))
            self.frame.imgzone.add_3D_points(ax, points)
        self.infotext.set(self.DESCRIPTION)
        self.points = all_points

    def scan_dump(self):
        to_dir = None
        if not self.is_calibrated.get():
            to_dir = tkFileDialog.askdirectory(mustexist=True, title="Choose destination")
            if not path.exists(to_dir):
                return
        return self.scan(to_dir)

    def scan(self, to_dir=None):
        self.points = None
        if self.is_calibrated.get():
            self.do_scan()
        else:
            self.infotext.set("Acquiring calibration image...")
            tkMessageBox.showinfo(
                "Calibration", 
                "The scanner is not calibrated yet. It will now take a sample "+
                "picture to determine initial lasers position. The image will "+
                "be displayed in the window. Please click on the image, in "+
                "order to align the red cross with the center of the yellow "+
                "cross, then click on \"Scan\" again."
            )
            self.scanner.arduino_dev = self.arduino.get()
            self.scanner.cam_id = int(self.camera.get())
            mask = self.scanner.calibrate()
            self.Cx, self.Cy = findCenter(mask)
            self.frame.imgzone.show_image((255*mask))
            self.scan_iter = self.scanner.scan(to_dir)
            self.infotext.set(self.DESCRIPTION)

    def open(self):
        self.infotext.set("Opening dump...")
        self.is_calibrated.set(False)
        from_dir = tkFileDialog.askdirectory(mustexist=True, title="Choose source directory")
        mask = self.scanner.calibrate_from(from_dir)
        if mask is None:
            tkMessageBox.showerror("File error", "Unable to open dump dir %s" % (from_dir))
        else:
            self.frame.imgzone.show_image((255*mask))
            tkMessageBox.showinfo(
                "Calibration", 
                "The image set is not calibrated yet. Please click on the image in "+
                "order to align the red cross on the center of the yellow cross. "+
                "Then, click on \"Scan\" to continue."
            )
            self.scan_iter = self.scanner.replay(from_dir)
        self.infotext.set("Need calibration")

    def save_config(self):
        filename = tkFileDialog.asksaveasfilename(defaultextension='.json', title="Save config")
        if filename:
            self.render_params.save(filename)

    def load_config(self):
        filename = tkFileDialog.askopenfilename(title="Load config")
        if filename:
            params = RenderParams.load(filename)
            self.Cx.set(float(params.CX)/self.scanner.W)
            self.Cy.set(float(params.CY)/self.scanner.H)
            self.H.set(params.H)
            self.L.set(params.L)
            self.LASER_L.set(params.LASER_L)
            self.LASER_R.set(params.LASER_R)
            self.THRES.set(params.THRES)
            self.is_calibrated.set(True)

    def export_obj(self):
        if self.points is None:
            tkMessageBox.showerror("No object", 
                "No 3D object to export. "+
                "You must first scan an object or replay a dump directory"
            )
        else:
            filename = tkFileDialog.asksaveasfilename(title="Export .obj")
            if filename:
                converter = ObjConverter(filename)
                converter.write(self.points)

if __name__ == "__main__":
    gui = App(Scanner())
    gui.mainloop()
    gui.destroy()

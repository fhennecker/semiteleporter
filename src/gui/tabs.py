import os
import glob
import logging
import threading
import Tkinter, ttk, tkFileDialog
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from mesher.voxel import Point

class Tab(Tkinter.Frame):
    def __init__(self, rootTab, title=""):
        """ Create a new 'abstract' Tab object
        rootTab = the Notebook reference
        title   = the name of the tab
        """
        self.rootTab = rootTab
        Tkinter.Frame.__init__(self, self.rootTab, width=800, height=600)
        self.rootTab.add(self, text=title)


class SetupTab(Tab):
    def __init__(self, rootTab, config):
        """ Create a new SetupTab object
        rootTab = the Notebook reference
        config  = the reference to the Config object from the Scanner
        """
        Tab.__init__(self, rootTab, "Setup")
        self.config  = config
        self.entries = dict()

        for i in range(6):
            self.rowconfigure(i, weight=1)
        for i in range(3):
            self.columnconfigure(i, weight=1)

        self.createSectionFrame("File").grid(row=0, column=0, columnspan=3)
        self.createSectionFrame("Arduino").grid(row=1, column=0, columnspan=3)
        self.createSectionFrame("Camera").grid(row=2, column=0, columnspan=3)
        self.createSectionFrame("LaserLeft").grid(row=3, column=0, columnspan=3)
        self.createSectionFrame("LaserRight").grid(row=4, column=0, columnspan=3)
        self.createSectionFrame("TurnTable").grid(row=5, column=0, columnspan=3)
        Tkinter.Button(self, text="Open", command=self.openConfigFile).grid(row=6, column=0, sticky='e')
        Tkinter.Button(self, text="Load", command=self.loadConfigFile).grid(row=6, column=1)
        Tkinter.Button(self, text="Save", command=self.saveConfigFile).grid(row=6, column=2, sticky='w')

    def createSectionFrame(self, section):
        frame = Tkinter.LabelFrame(self, text=section, font=("bold"))

        self.entries[section] = dict()
        line = 0
        for option in self.config[section]:
            value = self.config.getToStr(section, option)
            if(type(value) == list):
                varList = []
                Tkinter.Label(frame, text=option+" :").grid(row=line, column=0)
                line += 1
                for item,letter,col in zip(value, range(123-len(value),123), range(0,2*len(value),2)):
                    Tkinter.Label(frame, text=(chr(letter).upper()+" :")).grid(row=line, column=col)
                    varList.append(Tkinter.StringVar(frame, item))
                    Tkinter.Entry(frame, background="white", textvariable=varList[-1]).grid(row=line, column=col+1)
                self.entries[section][option] = varList
            else:
                Tkinter.Label(frame, text=option).grid(row=line, column=0)
                self.entries[section][option] = Tkinter.StringVar(frame, value)
                if(option == "port"):
                    path = self.entries[section][option].get()[:-1]+"*"
                    ttk.Combobox(frame, textvariable=self.entries[section][option], values=glob.glob(path), state='readonly', background="white").grid(row=line, column=1, padx=5, pady=5)
                else:
                    Tkinter.Entry(frame, background="white", textvariable=self.entries[section][option]).grid(row=line, column=1)
            line += 1
        return frame

    def refresh(self):
        for section in self.entries:
            for option in self.entries[section]:
                res = self.entries[section][option]
                if(type(res) == list):
                    for entry,idx in zip(res,range(len(res))):
                        entry.set(self.config[section][option][idx])
                else:
                    res.set(self.config[section][option])

    def openConfigFile(self):
        ext = None
        filename = None
        while(ext !=".cfg" and filename != ''):
            filename = tkFileDialog.askopenfilename(defaultextension=".cfg")
            ext = os.path.splitext(filename)[-1]
        if(filename != ''):
            self.config.load(filename)
            self.refresh()

    def loadConfigFile(self):
        logging.info("Loading Gui config to Config object")
        for section in self.entries:
            for option in self.entries[section]:
                res = self.entries[section][option]
                if(type(res) == list):
                    res = [res[0].get(),res[1].get(),res[2].get()]
                    self.config[section][option] = np.array(res, dtype=np.float32)
                else:
                    try:
                        self.config[section][option] = float(res.get())
                    except:
                        self.config[section][option] = res.get()

    def saveConfigFile(self):
        self.loadConfigFile()
        self.config.save()


class ViewerTab(Tab):
    def __init__(self, rootTab, scanner):
        """ Create a new ViewerTab object
        rootTab = the Notebook reference
        scanner = the Scanner reference
        """
        Tab.__init__(self, rootTab, "Viewer")

        self.scanner = scanner
        self.graph   = None
        self.axis    = None
        self.createGraph()
        self.createOptions()

    def createGraph(self, init=True):
        if(init):
            self.figure = plt.figure()
            self.graph = FigureCanvasTkAgg(self.figure, master=self)
            self.graph.get_tk_widget().grid(row=0, column=0)
            self.axis = self.figure.add_subplot(111, projection='3d')
        else:
            self.axis.clear()
        self.axis.set_xlabel('X axis')
        self.axis.set_xlim3d(-250,250)
        self.axis.set_ylabel('Y axis')
        self.axis.set_ylim3d(-250,250)
        self.axis.set_zlabel('Z axis')
        self.axis.set_zlim3d(0,500)
        self.graph.show()

    def createOptions(self):
        frame = Tkinter.LabelFrame(self, text="Options", font=("bold"))
        frame.grid(row=0, column=1)
        Tkinter.Button(frame, text="Start", command=self.start).grid(row=0, column=0)
        Tkinter.Button(frame, text="Export", command=self.export).grid(row=1, column=0)
        Tkinter.Button(frame, text="Mesh", command=self.mesh).grid(row=2, column=0)
        Tkinter.Button(frame, text="Quit", command=self.winfo_toplevel().destroy).grid(row=3, column=0)

    def _objSaveDialog(self):
        filename, ext = None, None
        while ext != ".obj" and filename != '':
            filename = tkFileDialog.asksaveasfilename(defaultextension=".obj")
            ext = os.path.splitext(filename)[-1]
        return filename

    def export(self):
        filename = self._objSaveDialog()
        if filename != "":
            self.scanner.exportToObjFile(filename)

    def start(self):
        self.scanner.startScan()
        self.plot()

    def plot(self, scene=None, lock=None):
        if(lock == None):
            self.createGraph(False)
            logging.info("Start plotting")
            lock = threading.Lock()
            thread_left = threading.Thread(target=self.plot, args=(self.scanner.sceneLeft, lock))
            thread_right = threading.Thread(target=self.plot, args=(self.scanner.sceneRight, lock))
            thread_left.start()
            thread_right.start()
        else:
            for slice in scene:
                arrays = map(Point.toNPArray, slice[0])
                
                if(len(arrays) != 0):
                    x, y, z = zip(*arrays)
                    lock.acquire()
                    self.axis.scatter(x, y, z, c='b', marker='.', s=2)
                    self.graph.draw()
                    lock.release()

    def mesh(self):
        filename = self._objSaveDialog()
        if filename != "":
            self.scanner.meshToObjFile(filename)

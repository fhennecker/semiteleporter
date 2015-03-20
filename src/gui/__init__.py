import logging
import Tkinter, ttk, tkMessageBox
from tabs import ViewerTab, SetupTab
import cv2


class Gui(Tkinter.Tk):
    def __init__(self, scanner):
        """ Create a new Gui object
        scanner = reference to the Scanner object
        """
        logging.info("Starting Gui")
        Tkinter.Tk.__init__(self, None)

        self.title("Scanner 3D")
        self.rootTab   = ttk.Notebook(self)
        self.rootTab.pack(fill='both',expand=True)
        self.viewerTab = ViewerTab(self.rootTab, scanner)
        self.setupTab  = SetupTab(self.rootTab, scanner.config)

        self.protocol('WM_DELETE_WINDOW', exit)

    def popUpConfirm(self, title, info):
        tkMessageBox.showinfo(title, info)
        self.update()

    def run(self):
        self.mainloop()

    def exit(self):
        self.destroy()
        self.quit()

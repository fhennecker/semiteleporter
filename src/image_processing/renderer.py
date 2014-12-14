from pipeline import Pipeline, EndOfProcessing
from douglaspeucker import reduce_pointset
from titriangulation import triangulation
from filter import findPoints
from math import atan
import multiprocessing
import Queue

class RenderParams(object):
    def __init__(self, L=350, H=55, LASER_L_X=-155, LASER_R_X=155, CX=960, CY=540, THRES=1):
        self.L = float(L)
        self.H = float(H)
        self.GAMMA_L = atan(LASER_L_X/self.L)
        self.GAMMA_R = atan(LASER_R_X/self.L)
        self.CX = int(CX)
        self.CY = int(CY)
        self.THRES = float(THRES)

class Renderer(multiprocessing.Process):
    def __init__(self, OPTIONS, scan_iterator):
        super(Renderer, self).__init__()
        self.left_pipe = Pipeline(
            lambda angle, im1, im2: (angle, findPoints(im1, im2)),
            triangulation(OPTIONS.L, OPTIONS.H, OPTIONS.CX, OPTIONS.CY, OPTIONS.GAMMA_L),
            lambda points: reduce_pointset(points, thres=OPTIONS.THRES)
        )
        self.right_pipe = Pipeline(
            lambda angle, im1, im2: (angle, findPoints(im1, im2)),
            triangulation(OPTIONS.L, OPTIONS.H, OPTIONS.CX, OPTIONS.CY, OPTIONS.GAMMA_R),
            lambda points: reduce_pointset(points, thres=OPTIONS.THRES)
        )
        self.scan_iterator = scan_iterator

    def __iter__(self):
        self.left_pipe.start()
        self.right_pipe.start()
        self.start()
        waiting = [self.left_pipe, self.right_pipe]
        while len(waiting) > 0:
            for pipe in waiting:
                try:
                    retired = pipe.output.get(False, 0.001)
                    if retired[0] == EndOfProcessing:
                        waiting.remove(pipe)
                        break
                    else:
                        yield retired
                except Queue.Empty:
                    pass
        self.left_pipe.terminate()
        self.right_pipe.terminate()
        self.join()

    def run(self):
        for angle, off, left, right in self.scan_iterator:
            self.left_pipe.feed(angle, left, off)
            self.right_pipe.feed(angle, right, off)
        self.left_pipe.feed(EndOfProcessing)
        self.right_pipe.feed(EndOfProcessing)

if __name__ == "__main__":
    from scanner import Scanner
    p = RenderParams(335, CX=972, CY=782)
    for points in Renderer(p, Scanner().replay("GLOBE")):
        print points


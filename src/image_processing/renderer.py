from pipeline import Pipeline, EndOfProcessing
from douglaspeucker import reduce_pointset
from titriangulation import triangulation
from filter import findPoints
from math import atan, tan
import multiprocessing
import Queue
import json

class RenderParams(object):
    SAVED_ATTRS = ('L', 'H', 'LASER_L', 'LASER_R', 'CX', 'CY', 'THRES')

    def __init__(self, L=350, H=55, LASER_L=-155, LASER_R=155, CX=960, CY=540, THRES=1):
        self.L = float(L)
        self.H = float(H)
        self.LASER_L = LASER_L
        self.LASER_R = LASER_R
        self.CX = int(CX)
        self.CY = int(CY)
        self.THRES = float(THRES)

    @property
    def GAMMA_L(self):
        return atan(self.L/abs(self.LASER_L))

    @property
    def GAMMA_R(self):
        return -atan(self.L/abs(self.LASER_R))

    def save(self, filename):
        with open(filename, 'w') as outFile:
            json.dump({
                name: getattr(self, name) for name in self.SAVED_ATTRS
            }, outFile)

    @classmethod
    def load(klass, filename):
        with open(filename) as inFile:
            data = json.load(inFile)
            return klass(**data)

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
                        yield retired[0]
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

def test_params_save_load():
    params = RenderParams(LASER_L=-42, LASER_R=24)
    params.save("/tmp/renderparams.json")
    copy = RenderParams.load("/tmp/renderparams.json")
    assert copy.LASER_L == -42
    assert copy.LASER_R == 24

if __name__ == "__main__":
    # Collect tests if not using py.test
    _ = locals()
    is_a_test = lambda x: x.startswith('test_') and '__call__' in dir(_[x])
    for test_name in filter(is_a_test, _.keys()):
        _[test_name]()

import multiprocessing
import traceback

class EndOfProcessing:
    pass

class PipeStage(multiprocessing.Process):
    def __init__(self, func, in_queue, out_queue=None):
        super(PipeStage, self).__init__()
        self.func = func
        self.input = in_queue
        self.output = out_queue

    def propagate(self, args):
        if self.output is not None:
            self.output.put(args)

    @property
    def name(self):
        return "Stage %s (%s)" % (self.func.__name__, hex(id(self)))

    def run(self):
        while True:
            args = self.input.get()
            if args[0] == EndOfProcessing:
                break
            else:
                try:
                    res = self.func(*args)
                except:
                    traceback.print_exc()
                    break

                if res is None:
                    res = tuple()
                elif type(res) != tuple:
                    res = (res,)
                self.propagate(res)
        self.propagate((EndOfProcessing,))

class Pipeline:
    """
    A class for chaining functions in multiple system threads.

    Example: given 3 functions
    f : A -> B
    g : B -> C
    h : C -> D

    a Pipeline(f, g, h) would run each function in a separate thread so that
    feeding A in the pipeline would produce D.
    """
    
    def __init__(self, *stages):
        """
        Create a new pipeline with given functions
        """
        self.stages = []

        self.input = multiprocessing.Queue()
        _in = self.input
        for stage in stages:
            out = multiprocessing.Queue()
            self.stages.append(PipeStage(stage, _in, out))
            _in = out

        self.output = self.stages[-1].output

    def feed(self, *args):
        """"""
        self.input.put(args)

    def retire(self):
        res = self.output.get()
        return res[0] if len(res) == 1 else res

    def retire_all(self):
        res = []
        retired = self.retire()
        while retired != EndOfProcessing:
            res.append(retired)
            retired = self.retire()
        return res

    def terminate(self):
        self.feed(EndOfProcessing)
        map(PipeStage.join, self.stages)

    def start(self):
        map(PipeStage.start, self.stages)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, type, value, traceback):
        """"""
        self.terminate()

    def __iter__(self):
        elem = self.retire()
        while elem != EndOfProcessing:
            yield elem
            elem = self.retire()

### Tests (to be moved elsewhere) ###

# Some functions to pipeline
plus = lambda a,b: a+b
mul3 = lambda x: 3*x

def test_pipeline_1stage():
    with Pipeline(plus) as pipe:
        pipe.feed(1, 3)
        pipe.feed(27, 15)
        assert pipe.retire() == 4
        assert pipe.retire() == 42
    assert pipe.retire() == EndOfProcessing

def test_pipeline_2stages():
    with Pipeline(plus, mul3) as pipe:
        pipe.feed(1, 3)
        assert pipe.retire() == 12
    assert pipe.retire() == EndOfProcessing

def test_pipeline_retire_after_terminate():
    pipe = Pipeline(plus)
    with pipe:
        pipe.feed(27, 15)
    assert pipe.retire() == 42
    assert pipe.retire() == EndOfProcessing

def test_pipeline_break():
    def func(*args):
        raise Exception()
        return "hello"
    with Pipeline(func) as pipe:
        pipe.feed("bite")
    assert pipe.retire() == EndOfProcessing

if __name__ == "__main__":
    # Collect tests if not using py.test
    _ = locals()
    is_a_test = lambda x: x.startswith('test_') and '__call__' in dir(_[x])
    for test_name in filter(is_a_test, _.keys()):
        print test_name
        _[test_name]()


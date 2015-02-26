import logging
import inspect
import multiprocessing


class EndOfProcessing:
    pass


class PipelineStage(multiprocessing.Process):
    def __init__(self, method, in_queue, out_queue):
        """ Create a new PipelineStage object
        method    = the method to apply
        in_queue  = the queue of inputs jobs
        out_queue = the queue of results
        """
        super(PipelineStage, self).__init__()
        self.method    = method
        self.in_queue  = in_queue
        self.out_queue = out_queue

    def run(self):
        args = self.in_queue.get()

        while(args != EndOfProcessing):
            try:
                nbrOfArgs = len(inspect.getargspec(self.method).args)-1
                res = (self.method(*args[:nbrOfArgs]),)+args[nbrOfArgs:]
                logging.debug("Process '%s' put a result" %(self.method.__name__))
                self.out_queue.put(res)
            except:
                logging.exception("Bad args format in PipelineStage '%s'" %(self.method.__name__))
            args = self.in_queue.get()
        self.out_queue.put(EndOfProcessing)
        logging.debug("Process '%s' down" %(self.method.__name__))


class Pipeline:
    def __init__(self, *methods):
        """ Create a new Pipeline object
        output  = the output container of the pipeline
        methods = all methods applied by the pipeline in the same order
        """
        self.in_queue = multiprocessing.Queue()
        self.out_queue = multiprocessing.Queue()
        self.stages   = []

        in_queue = self.in_queue
        out_queue = None
        for order in range(len(methods)):
            if(order == len(methods)-1):
                self.stages.append(PipelineStage(methods[order], in_queue, self.out_queue))
            else:
                out_queue = multiprocessing.Queue()
                self.stages.append(PipelineStage(methods[order], in_queue, out_queue))
                in_queue = out_queue

    def get(self):
        item = self.out_queue.get()
        if(item == EndOfProcessing):
            item = None
        return item
            
    def start(self):
        map(PipelineStage.start, self.stages)

    def feed(self, arg):
        self.in_queue.put(arg)

    def terminate(self):
        self.feed(EndOfProcessing)


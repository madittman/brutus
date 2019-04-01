import threading
from multiprocessing import Queue
from .core import Stage


"""
Definition of Pipeline
"""


class Pipeline(threading.Thread):
    """ Pipeline Class Handles Stages / Processing Steps. """

    def __init__(self, first_stage: Stage, file_type: str, contents_path: str):
        super(Pipeline, self).__init__()
        self.first_stage = first_stage  # Linked list of stages
        self.file_type = file_type  # File type of file that is to process (JPEG, ELF ect.)
        self.contents_path = contents_path  # Path where contents can be stored by stages
        self.proc_content = None
        self.queue = Queue()  # Tracked data objects are put in here so that the pipeline can access them

    def add_to_queue(self, filename: str):
        self.queue.put(filename)

    def output(self):
        return self.proc_content

    # Initiate pipeline processing by taking one filename out of the queue and processing it
    def run(self):
        print("==== Starting", self.file_type + "-Pipeline" + "...")

        # "/END/" indicates that there are no more filenames to collect
        for filename in iter(self.queue.get, "/END/"):
            print("\n==== %s got '%s'" % (self.file_type + "-Pipeline", filename.split('/')[-1]))

            self.first_stage.set_name(filename)
            self.first_stage.set_contents_path(self.contents_path)
            self.first_stage.start()  # Initiate pipeline processing by calling start method of first stage
            self.proc_content = self.first_stage.output()
            print("\n==== %s finished to process '%s'" % (self.file_type + "-Pipeline", filename.split('/')[-1]))  # TRACING

        print("\n==== %s exiting..." % (self.file_type + "-Pipeline"))  # TRACING

import magic
import os
import time
from glob import iglob
from .core import Harvester, pipeline_by_file_type

"""
Concrete implementation of Harvester class
"""


class FileHarvester(Harvester):
    """ Concrete Implementation of Harvester Class. """

    def __init__(self, path: str, file_types: list):
        Harvester.__init__(self)
        self.path = os.path.abspath(path)  # Path where to harvest files from
        self.file_endings = ["*"]
        self.file_types = file_types
        self.recursive = True

    def reset(self):
        self.file_endings = ["*"]
        self.file_types = []
        self.recursive = True

    # Setter for recursive
    def set_recursive(self, recursive):
        self.recursive = recursive

    # Getter, Setter for path
    def get_path(self):
        return self.path

    def set_path(self, path):
        self.path = path

    # Setter, Add for endings
    def set_endings(self, endings):
        self.file_endings = endings

    def add_ending(self, ending):
        self.file_endings.append(ending)

    # Setter, Add for file types
    def set_types(self, types):
        self.file_types = types

    def add_type(self, type):
        self.file_types.append(type)

    # Collect all filenames and filter filenames that don't match a file ending in self.file_types
    def run(self):
        print("Starting FileHarvester...")  # TRACING

        if self.recursive:
            self.path = os.path.join(self.path, "**/")
        for ext in self.file_endings:
            for filename in iglob(os.path.join(self.path, ext), recursive=self.recursive):
                with magic.Magic() as m:
                    for tp in self.file_types:
                        if m.id_filename(filename).startswith(tp):
                            print("\nPutting '%s' in '%s' queue" % (filename.split('/')[-1], tp))  # TRACING
                            # Insert tracked filename into appropriate pipeline queue
                            pipeline_by_file_type[tp].add_to_queue(filename)
                            self.crop.append(filename)  # Add tracked filename to crop
                            break

        for file_type, pipeline in pipeline_by_file_type.items():
            # "/END/" indicates that there are no more filenames to collect
            pipeline_by_file_type[file_type].add_to_queue("/END/")

        print("\nFileHarvester exiting...")  # TRACING

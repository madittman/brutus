import configparser
import json
import os
import hashlib
from .PipelineController import PipelineController
# Need to know each possible subclass of Harvester and Sampler for dynamic creation
from .FileHarvester import FileHarvester
from .DiskImageSampler import DiskImageSampler

"""
The Initiate class checks if a session of pipeline processing has already run, reads config file in
and passes its parameters to the components (Harvester, PipelineController, Sampler), respectively.
"""


class Initiate():
    """ Implementation of Initiate Class. """

    def __init__(self, conf_filename: str):
        config = configparser.ConfigParser()
        config.read_file(open(conf_filename))
        paths = config["Paths"]
        components = config["Components"]
        # Path where to harvest files from
        self.harvest_path = paths["source"]
        # Name of JSON file to customize process (can also be a path)
        self.json_file = paths["json_file"]
        # Path where "contents folder" is created
        # (folder where contents are written to and where Sampler retrieves its contents)
        self.contents_path = paths["stored_contents"]
        # Path where image and truth map are written to
        self.image_path = paths["destination"]

        # Names of concrete Harvester and Sampler class
        self.harvester_name = components["harvester"]
        self.sampler_name = components["sampler"]

        # The parameters for Harvester, pipelines and Sampler
        self.file_types = None
        self.pipelines = None
        self.sampler_arguments = None
        # Read parameters of JSON file
        self._read_config()
        # Check if session has already run and start new session if false
        if not self._has_session_run():
            self._start_session()

    # Define Sampler and create image as well as truth map
    def start_sampler(self):
        image_size = self.sampler_arguments["size"][0]
        # Boolean value whether file chunks are supposed to be merged in image or not
        merge_chunks = self.sampler_arguments["merge"][0]
        # Get ABCMeta class that represents the Sampler
        sampler_class = globals()[self.sampler_name]
        # Create instance of Sampler class
        sampler = sampler_class(image_size, self.contents_path, self.image_path, merge_chunks)
        sampler.generate_image()
        sampler.fill_truth_map()

    # Read parameters of JSON file
    def _read_config(self):
        with open(self.json_file) as definitions:
            all_config = json.load(definitions)  # Load all definitions
            self.file_types = all_config["harvester"]
            self.pipelines = all_config["pipelines"]
            self.sampler_arguments = all_config["sampler"]

    # Return True if session has already run, otherwise False
    def _has_session_run(self):
        all_files = []
        # Parse directory tree recursively and hash files to check any modification
        for root, subdirs, files in os.walk(self.harvest_path):
            all_files.extend(files)
        # Sort filenames so that list of same elements always stays the same
        all_files.sort()
        # Concatenate sorted filenames
        all_files = "".join(all_files)
        # Read in content of JSON file
        with open(self.json_file, 'r') as file:
            content_json = file.read()
        hashed_file_list = hashlib.sha256(bytes(all_files, "utf-8")).hexdigest()  # Hash of file list
        hashed_JSON_content = hashlib.sha256(bytes(content_json, "utf-8")).hexdigest()  # Hash of JSON content
        # Name of "contents folder" is truncated hash of file list and truncated hash of JSON content
        self.contents_path = os.path.join(os.getcwd(), str(hashed_file_list)[:10] + '_' + str(hashed_JSON_content)[:10])
        # Check if session has already run (if folder exists), otherwise create new folder in current path
        if not os.path.exists(self.contents_path):
            os.makedirs(self.contents_path)
            return False
        print("Session has already run.")
        return True

    def _start_session(self):
        # Get ABCMeta class that represents the Harvester
        harvester_class = globals()[self.harvester_name]
        # Create instance of Harvester class
        harvester = harvester_class(self.harvest_path, self.file_types)
        # Set PipelineController
        pipe_controller = PipelineController(harvester, self.file_types, self.pipelines, self.contents_path)
        # Start all pipelines with their stages
        pipe_controller.start_all_pipelines()

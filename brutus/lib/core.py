import threading
import os
import _io
from abc import ABCMeta, abstractmethod
from random import randint, shuffle

"""
Module of brutus core classes.
Definition of abstract core classes:
    Harvester
    Stage
    Sampler
Definition of core classes:
    Content
    ChunksOfFile
    Chunk
"""


# Global "file type, pipeline"-dictionary
pipeline_by_file_type = {}


class Harvester(threading.Thread, metaclass=ABCMeta):
    """ Basic Harvester Class. See Concrete Implementation for Details. """

    def __init__(self):
        super(Harvester, self).__init__()
        self.crop = []  # Maintain list of harvested objects (e.g. filenames etc)

    @abstractmethod
    def run(self):
        """ Abstract method. Overwrite by child classes necessary. """
        pass

    def get_crop(self):
        """ Return list of harvested objects. """
        return self.crop


class Stage(metaclass=ABCMeta):
    """ The Basic/Abstract Class Definition of a Stage.
    Representing a Stage/Processing Step in a Pipeline. """

    def __init__(self, args: list):
        self.args = args  # args are optional parameters for subclasses
        # Needing name for identification (e.g. filename of processed object)
        self.object_name = None
        # Path where contents can be written to
        self.contents_path = None
        # Next stage in pipeline
        self.next_stage = None

    # Getter, Setter for object name
    def get_name(self):
        return self.object_name

    def set_name(self, object_name):
        self.object_name = object_name

    # Getter, Setter for contents path
    def get_contents_path(self):
        return self.contents_path

    def set_contents_path(self, contents_path):
        self.contents_path = contents_path

    # Add next stage in Stage for the pipeline
    def add_stage(self, next_stage):
        """
        Args:
            next_stage: Following stage within the pipeline.
        """
        self.next_stage = next_stage

    # Test if Stage object has a next stage
    def has_next_stage(self):
        """
        Returns:
            True - if stage has next stage.
            False - if stage has no next stage.
        """
        return self.next_stage is not None

    # Execute pre-processing
    def _do_pre(self, contents):
        """
        :param contents: Content to pre-process.
        :returns: The processed content.
        """
        if self.count_pre > 0:
            for pre in self.pre_proc:
                contents = pre.process(contents)
        return contents

    # Main stage processing function
    # Has to be overwritten by concrete child classes
    @abstractmethod
    def _do_main(self, contents):
        """
        :param contents: Content to process.
        :returns: Processed content.
        """
        return contents

    # Execute post-processing
    def _do_post(self, contents):
        """
        :param contents: Content to pre-process.
        :returns: The processed content.
        """
        if self.count_post > 0:
            for post in self.post_proc:
                contents = post.process(contents)
        return contents

    # Step through all pipeline stages
    def process(self, contents, object_name, contents_path):
        """
        Process the stage and initiate the processing by the next stage.
        :param contents: The content to process.
        :returns: The processed contents.
        """

        # Name of processed object for next stage
        self.object_name = object_name
        # Path where to write contents to for next stage
        self.contents_path = contents_path
        contents = self._do_pre(contents)
        contents = self._do_main(contents)
        contents = self._do_post(contents)
        if self.has_next_stage():
            contents = self.next_stage.process(contents, self.object_name, self.contents_path)
        return contents


class Sampler(metaclass=ABCMeta):
    """ Basic Abstract Sampler Class. """

    # Set image size and path where contents are stored
    def __init__(self, size: int, contents_path: str, image_path: str, merge_chunks: bool):
        # Convert image size from megabytes to bytes
        self.size = size * 1000000
        # Set path where contents are stored
        self.contents_path = os.path.abspath(contents_path)
        # Set path where image will be stored
        self.image_path = image_path
        # Boolean value indicating whether single chunks of a file are shuffled in image or not
        self.merge_chunks = merge_chunks

        self.carving_image = bytearray()
        self.files = []  # list of ChunksOfFile

    # Generate carving image
    @abstractmethod
    def generate_image(self):
        return

    # Distribute contents (chunks or files) randomly in image
    def _distribute_contents(self):
        # Either chunks or files are the contents to distribute
        if not self.merge_chunks:
            self.all_chunks = []
            for file in self.files:
                # Get single chunks of all files (don't separate by file)
                self.all_chunks.extend(file.get_chunks())
            all_contents = self.all_chunks
        else:
            all_contents = self.files

        shuffle(all_contents)
        available_size = len(self.carving_image) - self.reserved_size
        gap_positions = sorted([randint(0, available_size) for i in range(len(all_contents))])
        position = last_gap_position = 0
        for content in all_contents:
            gap_position = gap_positions.pop(0)  # Get the next gap
            position += gap_position - last_gap_position  # Skip the next distance between gap positions
            self.carving_image[position: position + len(content)] = content.get_content()

            if not self.merge_chunks:
                # Set offset in Chunk object
                content.set_offset(position)
            else:
                # Set offsets in all Chunk objects
                content.set_offsets(position)

            position += len(content)
            last_gap_position = gap_position

    # Fill the truth map
    @abstractmethod
    def fill_truth_map(self):
        return


class Content(metaclass=ABCMeta):
    """ Basic Abstract Content Class. """

    def __init__(self, filename=None):
        self.filename = filename
        self.offset = None

    @abstractmethod
    def __len__(self):
        return

    def get_filename(self):
        return self.filename

    def get_offset(self):
        return self.offset

    @abstractmethod
    def get_content(self):
        return

    # Method for writing information of contents to truth map line by line
    @abstractmethod
    def write_out(self, map_file):
        return


class ChunksOfFile(Content):
    """ Class That Has All Chunks of One File. """

    def __init__(self, filename):
        Content.__init__(self, filename)
        self.chunks = []  # List of Chunk objects
        self._obtain_chunks()  # Build up Chunk list
        self.offset = self.chunks[0].get_offset()

    # Return total size of all chunks
    def __len__(self):
        return sum(map(len, self.chunks))

    # Collect all chunks with attributes in current path and set self.chunks
    def _obtain_chunks(self):
        pos_number = 1
        chunk_name = self.filename + "_" + str(pos_number)  # Name of first chunk file

        # Create Chunk object as long as next chunk exists (first chunk always exists)
        while os.path.isfile(chunk_name):
            chunk = Chunk()
            # Set chunk bytes to content in Chunk object
            with open(chunk_name, mode='rb') as chunk_file:
                chunk.set_content(chunk_file.read())
            chunk.set_pos_number(pos_number)
            chunk.set_filename(self.filename)
            # Set hashed content in Chunk object
            with open(os.path.join(os.getcwd(), "SHA-256 hashes", self.filename+".txt"), 'r') as hashes:
                hashed_content = hashes.read().split('\n')[pos_number - 1]
                chunk.set_sha256(hashed_content)
            # Add Chunk object to Chunk list
            self.chunks.append(chunk)
            # Next chunk name comes with incremented position number
            pos_number += 1
            chunk_name = self.filename + "_" + str(pos_number)

    def get_chunks(self):
        return self.chunks

    # Return bytearray of all concatenated chunks
    def get_content(self):
        file_content = bytearray()
        for chunk in self.chunks:
            file_content += chunk.get_content()
        return file_content

    # Set offsets of all Chunk objects (used when chunks stick together in storage)
    def set_offsets(self, position):
        for chunk in self.chunks:
            chunk.set_offset(position)
            position += len(chunk)

    # Write information of all chunks to truth map line by line
    def write_out(self, map_file):
        for chunk in self.chunks:
            chunk.write_out(map_file)


class Chunk(Content):
    """ Class That Represents a Split Piece of a File.
    Its Attributes Can Later Be Written out to the Truth Map. """

    def __init__(self):
        Content.__init__(self)
        self.content = bytearray()
        self.pos_number = 0  # Number of chunk
        self.offset = 0  # Byte position in carving image
        self.filename = str()
        self.sha256 = str()  # SHA256 hash of content

    # Return number of bytes in content
    def __len__(self):
        return len(self.content)

    def __str__(self):
        return "{},\t{} B,\t{},\t{},\t{}".format(self.pos_number, len(self), self.offset, self.filename, self.sha256)

    def get_content(self):
        return self.content

    def set_content(self, content):
        self.content = content

    def get_pos_number(self):
        return self.pos_number

    def set_pos_number(self, pos_number):
        self.pos_number = pos_number

    def set_offset(self, offset):
        self.offset = offset

    def set_filename(self, filename):
        self.filename = filename

    def get_sha256(self):
        return self.sha256

    def set_sha256(self, sha256):
        self.sha256 = sha256

    # Write line of chunk information to truth map
    def write_out(self, map_file: _io.TextIOWrapper):
        map_file.write(str(self) + '\n')

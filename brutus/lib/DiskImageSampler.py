import os
import glob
import numpy
from .core import Sampler, ChunksOfFile


"""
Definition of DiskImageSampler
"""


class DiskImageSampler(Sampler):
    """  Concrete Implementation of Sampler Class for Generating Disk Images. """

    def __init__(self, size: int, contents_path: str, image_path: str, merge_chunks: bool):
        Sampler.__init__(self, size, contents_path, image_path, merge_chunks)
        self.image_path = os.path.join(self.image_path, "Disk Image")
        # Create "Disk Image" folder if it doesn't exist yet
        if not os.path.exists(self.image_path):
            os.makedirs(self.image_path)

        #self.files = []  # list of ChunksOfFile
        #self.carving_image = bytearray()
        self.all_chunks = []

        # Create empty truth map
        with open(os.path.join(self.image_path, "truth_map.txt"), 'w') as truth_map:
            columns = "{},\t{},\t{},\t{},\t{}\n\n".format("Number", "Size", "Chunk Offset", "File", "SHA-256 Hash")
            truth_map.write(columns)

        # Obtain list of ChunkOfFile objects
        self._obtain_files()

    # Obtain list of ChunkOfFile objects
    # (stored chunks are read in automatically by ChunksOfFile constructor)
    def _obtain_files(self):
        current_path = os.getcwd()  # Save current path in order to go back later
        os.chdir(self.contents_path)  # Go to contents directory

        # Remove number including underscore in filenames (e.g. abc.jpg_1 -> abc.jpg)
        # (For each file there is at least one chunk with number 1)
        for filename in glob.glob("*_1"):
            filename = filename.split('_')
            filename.pop()  # Remove number in filename
            filename = '_'.join(filename)  # Merge elements again in case filename contained underscore
            file = ChunksOfFile(filename)  # This obtains the chunks automatically
            self.files.append(file)

        os.chdir(current_path)  # Go back to previous directory

    # Generate disk image out of random bytes and spread chunks/files in it
    def generate_image(self):
        # Check if sum of all chunks is larger than disk image's size
        self.reserved_size = sum(map(len, self.files))
        if self.reserved_size > self.size:
            # Delete empty truth map and "Disk Image" folder
            os.unlink(os.path.join(self.image_path, "truth_map.txt"))
            os.rmdir(self.image_path)
            raise Exception("Disk image too small for files. It must have at least %f MB."
                            % (self.reserved_size / 10**6))
        # Generate random bytearray
        print("\n==== Generating Disk Image...")  # TRACING
        self.carving_image = bytearray(numpy.random.bytes(self.size))

        # Distribute chunks/files randomly in disk image
        self._distribute_contents()

        # Write disk image onto storage
        with open(os.path.join(self.image_path, "disk_image.img"), 'wb') as image_file:
            image_file.write(self.carving_image)
        print("\n==== Disk Image has been written to", self.image_path)  # TRACING

    def fill_truth_map(self):
        # Either chunks or files are the contents to write out
        if not self.merge_chunks:
            all_contents = self.all_chunks
        else:
            all_contents = self.files
        # Sort all contents (chunks or files) by offset
        all_contents.sort(key=lambda x: x.offset)
        with open(os.path.join(self.image_path, "truth_map.txt"), 'a') as truth_map:
                # Write out content information line by line
                for content in all_contents:
                    content.write_out(truth_map)
        print("\n==== Truth Map has been written to", self.image_path)  # TRACING

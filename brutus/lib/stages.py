import magic
import os
import hashlib
import struct
from .core import Stage

"""
Stage Subclasses:
    File,
        FileELF, FileJPEG, Noise
    HeaderJPEG
    Fragment,
        Split
    SaveHashes
    Processed,
        DiskImage, SendTCP, SendUDP
"""


"""
Stages:
    File
    FileELF
    FileJPEG
    Noise
"""

class File(Stage):
    """ Initiating Stage for Reading in a General File. """

    def __init__(self, args):
        Stage.__init__(self, args)
        self.file_content = None
        self.file_hash = None
        self.file_type = None
        # Processed content is saved separately
        self.proc_content = None

    # Initiate pipeline processing
    def start(self):
        self.proc_content = self.process([self.file_content], self.object_name, self.contents_path)

    def get_hash(self):
        return self.file_hash.hexdigest()

    def get_type(self):
        return self.file_type

    def output(self):
        return self.proc_content

    def _do_pre(self, contents):
        #print("File _do_pre")  # TRACING
        with open(self.object_name, mode='rb') as file:
            self.file_content = file.read()  # Read in whole file in binary mode
            self.file_hash = hashlib.sha256(self.file_content)  # (Not important for now)
        # Determine type for input file
        with magic.Magic() as m:
            self.file_type = m.id_filename(self.object_name)
        # Contents need to be a list of bytearrays to do modification
        byte_stream = bytearray(self.file_content)
        contents = []
        contents.append(byte_stream)
        return contents  # Return list of bytearrays

    def _do_main(self, contents):
        #print("File _do_main")  # TRACING
        return contents

    def _do_post(self, contents):
        #print("File _do_post")  # TRACING
        return contents


class FileELF(File):
    """ Class for ELF Binary. """

    def __init__(self, args):
        File.__init__(self, args)

    def _do_pre(self, contents):
        #print("FileELF _do_pre")  # TRACING
        contents = super()._do_pre(contents)
        return contents

    def _do_main(self, contents):
        #print("FileELF _do_main")  # TRACING
        contents = super()._do_main(contents)
        return contents

    def _do_post(self, contents):
        #print("FileELF _do_post")  # TRACING
        contents = super()._do_post(contents)
        return contents


class FileJPEG(File):
    """ Class for JPEG Binary. """

    def __init__(self, args):
        File.__init__(self, args)

    def _do_pre(self, contents):
        #print("FileJPEG _do_pre")  # TRACING
        contents = super()._do_pre(contents)
        return contents

    def _do_main(self, contents):
        #print("FileJPEG _do_main")  # TRACING
        contents = super()._do_main(contents)
        return contents

    def _do_post(self, contents):
        #print("FileJPEG _do_post")  # TRACING
        contents = super()._do_post(contents)
        return contents


class Noise(File):
    """ Class for Setting Noise in File. """

    def __init__(self, args):
        File.__init__(self, args)
        if len(self.args) == 0:
            self.offset = 100  # Write 0 to every 100th byte in each content by default
        elif len(self.args) == 1:
            self.offset = self.args[0]  # Parameter is byte distance between zeros
        else:
            raise Exception('Too many arguments in "Noise".')

    def _do_pre(self, contents):
        #print("Noise _do_pre")  # TRACING
        return contents

    def _do_main(self, contents):
        #print("Noise _do_main")  # TRACING
        for idx, content in enumerate(contents):
            current_byte = self.offset - 1
            while current_byte < len(content):
                # (Equal to 'contents[idx][current_byte] = 0')
                struct.pack_into('b', contents[idx], current_byte, 0)
                current_byte += self.offset
        return contents

    def _do_post(self, contents):
        #print("Noise _do_post")  # TRACING
        return contents


"""
Stages:
    HeaderJPEG
"""

class HeaderJPEG(FileJPEG):
    """ Class for Removing First 100 Bytes from JPEG File.
    This Only Makes Sense If File Is Not Already Split. """

    def __init__(self, args):
        FileJPEG.__init__(self, args)

    def _do_pre(self, contents):
        #print("HeaderJPEG _do_pre")  # TRACING
        return contents

    def _do_main(self, contents):
        #print("HeaderJPEG _do_main")  # TRACING
        # Remove first 100 bytes (of each content)
        for content in contents:
            del content[:100]
        return contents

    def _do_post(self, contents):
        #print("HeaderJPEG _do_post")  # TRACING
        return contents


"""
Stages:
    Fragment
    Split
"""

class Fragment(Stage):
    """ Class for a Fragment. """

    def __init__(self, args):
        Stage.__init__(self, args)
        self.header = None
        self.body = None
        self.footer = None

    def __repr__(self):
        return self.hash.hexdigest()

    def _do_pre(self, contents):
        #print("Fragment _do_pre")  # TRACING
        return contents

    def _do_main(self, contents):
        #print("Fragment _do_main")  # TRACING
        return contents

    def _do_post(self, contents):
        #print("Fragment _do_post")  # TRACING
        return contents


class Split(Fragment):
    """ Class for Splitting File Content into Byte Blocks. """

    def __init__(self, args):
        Fragment.__init__(self, args)
        if len(self.args) == 0:
            self.size = 1000  # Standard split length are 1000 bytes
        elif len(self.args) == 1:
            self.size = self.args[0]  # Parameter is size of split
        else:
            raise Exception('Too many arguments in "Split".')

    def _do_pre(self, contents):
        #print("Split _do_pre")  # TRACING
        return contents

    def _do_main(self, contents):
        #print("Split _do_main")  # TRACING

        # Split content into byte blocks
        new_contents = []
        for content in contents:
            for i in range(0, len(content), self.size):
                new_contents.append(content[i:i + self.size])

        return new_contents  # Return list of bytearrays

    def _do_post(self, contents):
        #print("Split _do_post")  # TRACING
        return contents


"""
Stages:
    SaveHashes
"""

class SaveHashes(Stage):
    """ Class for Creating Text File to Save Hashes After File Has Been Split. """

    def __init__(self, args):
        Stage.__init__(self, args)

    def _do_pre(self, contents):
        #print("SaveHashes _do_pre")  # TRACING
        return contents

    def _do_main(self, contents):
        #print("SaveHashes _do_main")  # TRACING
        # Folder where hashes are saved in text files
        hashes_path = os.path.join(self.contents_path, "SHA-256 hashes")
        # Create "SHA-256 hashes" folder for saving hashes of chunks
        if not os.path.exists(hashes_path):
            os.makedirs(hashes_path)

        filename = self.object_name.split('/')[-1]  # Extract filename from path
        filename += ".txt"

        # Write hashes of chunks into text file
        with open(os.path.join(hashes_path, filename), 'a') as hashes_file:
            for content in contents:
                hashed_content = hashlib.sha256(content).hexdigest()
                hashes_file.write(hashed_content + '\n')

        return contents

    def _do_post(self, contents):
        #print("SaveHashes _do_post")  # TRACING
        return contents


"""
Stages:
    Processed
    DiskImage
    SendTCP
    SendUDP
"""

class Processed(Stage):
    """ The Major Processed Class to End a Pipeline Processing. """

    def __init__(self, args):
        Stage.__init__(self, args)

    def _do_pre(self, contents):
        #print("Processed _do_pre")  # TRACING
        return contents

    def _do_main(self, contents):
        #print("Processed _do_main")  # TRACING
        return contents

    def _do_post(self, contents):
        #print("Processed _do_post")  # TRACING
        return contents


class DiskImage(Processed):
    """ Class for Writing Contents to Disk Storage. """

    def __init__(self, args):
        Processed.__init__(self, args)

    def _do_pre(self, contents):
        #print("DiskImage _do_pre")  # TRACING
        return contents

    def _do_main(self, contents):
        #print("DiskImage _do_main")  # TRACING

        # Write single processed contents of file to contents path
        content_number = 1
        #print("-> Creating contents for", self.object_name)  # TRACING
        for content in contents:
            # Content name is the filename with a number that follows an underscore (i.e. filename.jpg_1)
            content_name = "%s_%d" % (self.object_name.split('/')[-1], content_number)

            with open(os.path.join(self.contents_path, content_name), 'wb') as file:
                file.write(content)

            content_number += 1

        return contents

    def _do_post(self, contents):
        #print("DiskImage _do_post")  # TRACING
        return contents


class SendTCP(Processed):
    """ Class for Sending Contents over TCP. """

    def __init__(self, args):
        Processed.__init__(self, args)

    def _do_pre(self, contents):
        return contents

    def _do_main(self, contents):
        return contents

    def _do_post(self, contents):
        return contents


class SendUDP(Processed):
    """ Class for Sending Contents over UDP. """

    def __init__(self, args):
        Processed.__init__(self, args)

    def _do_pre(self, contents):
        return contents

    def _do_main(self, contents):
        return contents

    def _do_post(self, contents):
        return contents

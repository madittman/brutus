from lib.Initiate import Initiate
import configparser


if __name__ == '__main__':

    # Harvest files in ../tests recursively, use definitions.json as configuration file
    # and current folder as "contents path"
    init = Initiate("configuration.cfg")
    # Create disk image folder in upper directory
    init.start_sampler()

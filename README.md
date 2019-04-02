# Brutus

A framework for generating test images out of input files.

## Getting Started

These instructions will get you a copy of the project up and running on your local machine for development and testing purposes. See deployment for notes on how to deploy the project on a live system.

### Prerequisites

*Python 3.6* is needed to run Brutus. Furthermore, the library *python-libmagic 0.4.0* is required.
<br />
The following command will install this library.

```
pip install python-libmagic
```

## Deployment

The purpose of this framework is to generate synthetic carving images that can be later examined by file carvers. One needs to select some input files which are then processed in pipelines. The processed file contents are stored on the disk. These can then be packed into a carving image.

### Main Components

The framework consists of several main components that make up the whole processing. The purpose of each component is explained in this section.

#### Initiate

The *Initiate* class is a helper class that starts the process of the other components. Its only argument is the path of the *configuration file* which is later explained. By creating an instance of *Initiate*, the files are processed in pipelines and the resulting file contents are stored on the disk. By using the method *start_sampler()*, a file carving image is generated and these file contents are packed into it.
<br />
It is not possible to generate a carving image without the pipeline processing having run once. The pipeline processing does not rerun if the input files and the file that defines this processing (a JSON file) stay exactly the same. This is guaranteed by joining a truncated hash of all concatenated filenames and a truncated hash of the JSON file's content. The result is the name of the folder that stores the outcome of the processed files. This folder remains on the disk even after the program has exited. Thus, *Initiate* creates these truncated hash values and checks if a folder with this name already exists.
<br />
If this is the case, no pipeline processing is built up and it is assumed that the folder still contains all processed file contents from a previous session. Otherwise, *Initiate* sets the parameters for the other components and starts the whole pipeline processing. The following code section shows how to initiate this process.

```
# Initiate the pipeline processing by using the configuration file
init = Initiate("configuration.cfg")
# Generate synthetic carving image
init.start_sampler()
```

#### Harvester

The *Harvester* class is a component that searches a folder for data objects and creates a list of objects that match a certain format. What formats the *Harvester* is supposed to track can be specified in the JSON file (later explained). The *Harvester* is an abstract class that needs to be implemented by subclasses. A concrete *FileHarvester* class is already implemented that is used to track files on the disk.

#### PipelineController

The *PipelineController* class is used to start the process of the pipelines.

#### Sampler

#### Stage

### Configuration File

### JSON File

### Framework Extensions


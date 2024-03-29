# Brutus

A framework for generating carving images out of input files.

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

The purpose of this framework is to generate synthetic carving images that can be later examined by file carvers. One needs to select some input files which are then processed in pipelines. The processed file contents are stored on the disk. These can then be packed into a carving image. A text file (called *truth map*) is also generated which indicates a list of the file contents and their offsets inside the carving image.

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

The *PipelineController* class is used to start the process of the pipelines. It knows the *Harvester* and all the necessary pipelines for the processing. It implements the producer-consumer pattern where the *Harvester* is the producer and the pipelines are the consumers. A pipeline can only process the files of one specific data type but all pipelines can work in parallel.

#### Sampler

The *Sampler* class is used to generate carving images out of the results of the pipeline processing. It is an abstract class but a concrete *DiskImageSampler* for generating disk images is already implemented. The *Sampler* also has a method for generating the truth map which is put into the same folder as the carving image.

#### Stage

The abstract *Stage* class represents a processing step in a pipeline. A stage has a pre-, main- and post-processing method. The stages of each data type need to be listed in the JSON file. A linked list of stages is automatically passed to a pipeline. A data object is passed on by the stages which is then processed step by step.

### Configuration File

The configuration file is a text file in which some paths are set as well as a concrete *Harvester* and *Sampler* class. An example is shown below.

```
[Paths]
source: ../tests
json_file: definitions.json
stored_contents: .
destination: .

[Components]
harvester: FileHarvester
sampler: DiskImageSampler
```

There are two sections: the *Paths* and the *Components*.
<br />
In the *Paths* section, the *source* is the path in which the *Harvester* collects the data objects. *json_file* is the path of the JSON file in which the pipeline processing is defined. *stored_contents* is the path where the processed outcomes of the files is stored and *destination* is the path in which the carving image is stored along with the truth map.
<br />
In the *Components* section, the *FileHarvester* is the name of a concrete *Harvester* class and *DiskImageSampler* is the name of a concrete *Sampler* class.
<br />
This file is read in by the *Initiate* class which builds up the components for the processing.

### JSON File

The JSON file is needed for some definitions of the pipeline processing. An example is shown below.

```
{
    "harvester": ["JPEG", "ELF", "PDF"],
    
    "pipelines":[
    {"stages":[ {"FileJPEG":[]}, {"HeaderJPEG":[]}, {"Split":[2000]}, {"SaveHashes":[]},
        {"Noise":[1000]}, {"DiskImage":[]} ] },
    {"stages":[ {"FileELF":[]}, {"Split":[]}, {"SaveHashes":[]}, {"DiskImage":[]} ] },
    {"stages":[ {"File":[]}, {"SaveHashes":[]}, {"Noise":[3000]}, {"DiskImage":[]} ] }
    ],
    
    "sampler":{"size":[10], "merge":[true]}
}
```

There are three sections: *harvester*, *pipelines* and *sampler*.
<br />
The *harvester* takes a list of the data types it is supposed to collect. In this case, these are *JPEG*, *ELF* and *PDF* files.
<br />
The *pipelines* take a list of stages. Each list of stages belongs to one data type and is assigned in the order they are listed in the *harvester* section. The squared brackets behind a stage name are used for optional arguments. In the example, a JPEG file is processed as follows.
<br />
First, it is read in by the initiating stage *FileJPEG*. Afterwards, the header of the file is removed by *HeaderJPEG*. Then, the file is split into contents of 2000 bytes each since this number is passed as an argument in *Split*. After that, the SHA256 hashes of each file content are saved in a folder on the disk for later purposes. They are finally written to the truth map. This is an important stage and without it, the truth map cannot be generated. The *Noise* stage replaces each 1000th byte by a zero. It also comes with an optional parameter representing the strength of the noise. Finally, the *DiskImage* stage is used to write out the processed file contents to the disk. This stage is necessary since these file contents need to be there for the *Sampler* which packs them into a carving image.
<br />
The *sampler* section takes two parameters for the *Sampler*. First, the size of the carving image is set. In this case, these are 10 megabytes. Secondly, it needs to be set wether the file contents are shuffled in the carving image or not. This only makes a difference, if the files have been split up. If *merge* is set to true, all the file contents that belong to one file are merged to one file again and are packed into the carving image sequently. However, if *merge* is set to false, all the file contents are intermingled and packed at random offsets inside the carving image.

### Framework Extensions

In order to extend the framework by a *Harvester* class, only the method *run()* needs to be implemented. The abstract *Harvester* class just comes with a list called *crop* which is used to collect the names of the harvested data objects. However, the *Harvester* is supposed to know the pipelines by a global dictionary *pipeline_by_file_type* in which the file types are the keys and the pipelines are the values. Every pipeline has its own queue where its data objects are supposed to be put in. Thus, a pipeline is woken up when the *Harvester* puts a new data object into its queue.
<br />
<br />
In order to define a new *Stage* class, it needs to be inherited by the abstract *Stage* class or by some other class which is a concrete implementation of the *Stage* class. A stage has three methods: *_do_pre()*, *_do_main()* and *_do_post()* but not all three need to be defined. There needs to be a starting stage which is the first element in the linked list which is passed to pipeline. The starting stage has a method *start()* which initiates the processing. Only *File* as well as *FileJPEG* and *FileELF* which are inherited by *File* are implemented as a starting stage.
<br />
The order of the stages is of course important. This needs to be kept track of when defining a new stage. For example, the stage *HeaderJPEG* cannot come after the stage *Split* which already splits up the file.
<br />
<br />
In order to extend the framework by a *Sampler* class, the methods *generate_image()* and *fill_truth_map()* need to be defined. There is already a method *_distribute_contents()* implemented which is used to set the offsets of the file contents randomly. In the *DiskImageSampler*, this method is called inside the *generate_image()* method.

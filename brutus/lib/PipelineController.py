from .core import Harvester, pipeline_by_file_type
from .Pipeline import Pipeline
from .stages import *  # Need to know each possible Stage subclass for building up Pipelines

"""
Definition of PipelineController
"""


class PipelineController():
    """ Controller for Different Pipelines.
    Interface Between Harvester and Pipelines.
    Implementing Producer-Consumer Pattern. """

    def __init__(self, harvester: Harvester, file_types: list, pipelines: list, contents_path: str):
        self.harvester = harvester
        self.file_types = file_types  # List of file types for each pipeline
        self.pipelines = pipelines
        # Path where contents can be written to by a pipeline stage
        self.contents_path = contents_path

    def reset(self):
        global pipeline_by_file_type
        self.harvester = None
        self.pipelines = None
        pipeline_by_file_type = {}

    # Getter, Setter for Harvester
    def get_harvester(self):
        return self.harvester

    def set_harvester(self, harvester):
        self.harvester = harvester

    # Getter, Setter, Add for pipelines
    def get_pipelines(self):
        return self.pipelines

    def set_pipelines(self, pipelines):
        self.pipelines = pipelines

    def add_pipeline(self, pipeline):
        self.pipelines.append(pipeline)

    # Load all necessary pipelines for harvested objects and let them work parallel
    def start_all_pipelines(self):
        global pipeline_by_file_type
        consumers = []
        # Each pipeline is a consumer
        num_consumers = len(self.pipelines)

        stages = []  # List of linked lists of stages for each pipeline
        for pipeline in self.pipelines:
            stages.append(self._create_stages(pipeline["stages"]))

        # Create consumer threads
        for i in range(num_consumers):
            pipe = Pipeline(stages[i], self.file_types[i], self.contents_path)
            pipeline_by_file_type[self.file_types[i]] = pipe  # Add pipeline instance to global dictionary
            consumers.append(pipe)

        # Start the producer and consumers
        self.harvester.start()
        for c in consumers:
            c.start()

        # Wait until threads terminate
        self.harvester.join()
        for c in consumers:
            c.join()

        print("\nPipelineController exiting...")  # TRACING

    # Create linked list of stages.
    # Stages are identified by names of Stage subclasses.
    # E.g.: stages = [{'FileJPEG': []}, {'HeaderJPEG': []}, {'Split': [1000]}, ...]
    @staticmethod
    def _create_stages(stages):
        previous_stage = None
        for stage in stages:
            stage_name = list(stage.keys())[0]  # Extract Stage name from dictionary
            parameters = stage[stage_name]  # A list of optional parameters for the stage
            stage_class = globals()[stage_name]  # Get ABCMeta class that represents the stage
            current_stage = stage_class(parameters)  # Create instance of Stage class
            # Save first stage
            if previous_stage is None:
                first_stage = current_stage
            # Add next node if a previous stage exists
            else:
                previous_stage.add_stage(current_stage)
            previous_stage = current_stage

        return first_stage  # Return linked list of stages

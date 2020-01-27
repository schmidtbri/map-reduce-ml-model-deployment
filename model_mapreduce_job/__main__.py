"""MapReduce job entry point."""
import os
import logging
import argparse

from model_mapreduce_job.model_manager import ModelManager
from model_mapreduce_job.config import Config
from model_mapreduce_job.ml_model_map_reduce_job import MLModelMapReduceJob

logging.basicConfig(level=logging.INFO)

# loading the configuration
configuration = __import__("model_mapreduce_job"). \
    __getattribute__("config"). \
    __getattribute__(os.environ["APP_SETTINGS"])

# loading the models into the ModelManager
model_manager = ModelManager()
model_manager.load_models(Config.models)


def main(model_qualified_name):
    """Execute a MapReduce job."""
    # creating the MrJob class that will run the MLModel class
    ml_model_map_reduce_job = MLModelMapReduceJob(model_qualified_name=model_qualified_name)
    ml_model_map_reduce_job.run()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Start an MLModel MapReduce job.')
    parser.add_argument('--model_qualified_name', type=str, help='Qualified name of the model.')

    args = parser.parse_args()

    main(model_qualified_name=args.model_qualified_name)

"""MapReduce job that hosts MLModel objects."""
import os
import logging
from mrjob.protocol import JSONProtocol, JSONValueProtocol
from mrjob.job import MRJob

from model_mapreduce_job.config import Config
from model_mapreduce_job.model_manager import ModelManager

logging.basicConfig(level=logging.INFO)

# loading the configuration
configuration = __import__("model_mapreduce_job"). \
    __getattribute__("config"). \
    __getattribute__(os.environ["APP_SETTINGS"])

# loading the models into the ModelManager
model_manager = ModelManager()
model_manager.load_models(Config.models)


class MLModelMapReduceJob(MRJob):
    """MapReduce job definition."""

    INPUT_PROTOCOL = JSONValueProtocol
    OUTPUT_PROTOCOL = JSONProtocol

    # setting used to include package when running in AWS EMR
    DIRS = ['../model_mapreduce_job']

    def __init__(self, *args, **kwargs):
        """Initialize class."""
        super(MLModelMapReduceJob, self).__init__(*args, **kwargs)

        self._model = model_manager.get_model(self.options.model_qualified_name)

        if self._model is None:
            raise ValueError("'{}' not found in the ModelManager instance.".format(self.options.model_qualified_name))

    def configure_args(self):
        """Configure command line argument."""
        super(MLModelMapReduceJob, self).configure_args()
        self.add_passthru_arg('--model_qualified_name', type=str, help='Qualified name of the model.')

    def mapper(self, _, data):
        """Mapper function that makes prediction with an MLModel object."""
        # making a prediction
        prediction = self._model.predict(data=data)

        # yielding the prediction result
        yield data, prediction


if __name__ == '__main__':
    MLModelMapReduceJob.run()

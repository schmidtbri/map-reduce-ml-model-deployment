"""Class to host an MlModel object in a MapReduce job."""
import logging
import json
from mrjob.job import MRJob

from model_mapreduce_job import __name__
from model_mapreduce_job.model_manager import ModelManager

logger = logging.getLogger(__name__)


class MLModelMapReduceJob(MRJob):
    """Class for MLModel gRPC endpoints."""

    def __init__(self, model_qualified_name, **kwargs):
        """Create a MapReduce job for an MLModel object.

        :param model_qualified_name: The qualified name of the model that will be hosted in this endpoint.
        :type model_qualified_name: str
        :returns: An instance of MLModelMapReduceJob.
        :rtype: MLModelMapReduceJob
        """
        super().__init__(kwargs)

        model_manager = ModelManager()
        self._model = model_manager.get_model(model_qualified_name)

        if self._model is None:
            raise ValueError("'{}' not found in ModelManager instance.".format(model_qualified_name))

        logger.info("Initializing MapReduce job for model: {}".format(self._model.qualified_name))

    def mapper(self, _, line):
        """Mapper that makes a prediction using an MLModel object."""
        try:
            data = json.loads(line)
        except json.decoder.JSONDecodeError as e:
            yield None

        # making a prediction and serializing it to JSON
        prediction = self._model.predict(data=data)
        json_prediction = json.dumps(prediction)

        yield json_prediction

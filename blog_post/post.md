Title: A MapReduce ML Model Deployment
Date: 2020-02-23 09:25
Category: Blog
Slug: map-reduce-ml-model-deployment
Authors: Brian Schmidt
Summary: Because of the growing need to process large amounts of data across many computers, the Hadoop project was started in 2006. Hadoop is a set of software components that help to solve large scale data processing problems using clusters of computers. Hadoop supports mass data storage through the HDFS component and large scale data processing through the MapReduce component. Hadoop clusters have become a central part of the infrastructure of many companies because of their usefulness. In this blog post, we'll focus on the MapReduce component of Hadoop since we will be deploying a machine learning model, which is a compute-intensive process. MapReduce is a programming framework for data processing which is useful for processing large amounts of distributed data. MapReduce is able to handle errors and failures in the computation. MapReduce is also inherently parallel in nature but abstracts out that fact, making the code look like single-process code.

This blog post builds on the ideas started in
[three]({filename}/articles/a-simple-ml-model-base-class/post.md)
[previous]({filename}/articles/improving-the-mlmodel-base-class/post.md)
[blog posts]({filename}/articles/using-ml-model-abc/post.md).

In this blog post I'll show how to deploy the same ML model that l
deployed as a batch job in this [blog
post]({filename}/articles/etl-job-ml-model-deployment/post.md),
as a task queue in this [blog
post]({filename}/articles/task-queue-ml-model-deployment/post.md),
inside an AWS Lambda in this [blog
post]({filename}/articles/lambda-ml-model-deployment/post.md),
as a Kafka streaming application in this [blog
post]({filename}/articles/streaming-ml-model-deployment/post.md),
and a gRPC service in this [blog
post]({filename}/articles/grpc-ml-model-deployment/post.md).

The code in this blog post can be found in this [github
repo](https://github.com/schmidtbri/map-reduce-ml-model-deployment).

# Introduction

Because of the growing need to process large amounts of data across many
computers, the Hadoop project was started in 2006. Hadoop is a set of
software components that help to solve large scale data processing
problems using clusters of computers. Hadoop supports mass data storage
through the HDFS component and large scale data processing through the
MapReduce component. Hadoop clusters have become a central part of the
infrastructure of many companies because of their usefulness.

In this blog post, we'll focus on the MapReduce component of Hadoop
since we will be deploying a machine learning model, which is a
compute-intensive process. MapReduce is a programming framework for data
processing which is useful for processing large amounts of distributed
data. MapReduce is able to handle errors and failures in the
computation. MapReduce is also inherently parallel in nature but
abstracts out that fact, making the code look like single-process code.

Hadoop and MapReduce are used to process large data sets almost
exclusively. Even though machine learning models are trained over large
data sets, we'll focus on using MapReduce to execute predictions. Hadoop
and MapReduce should be considered when a prediction batch job needs to
be executed on millions or billions of records. This blog post is
similar to [a previous blog
post]({filename}/articles/etl-job-ml-model-deployment/post.md)
that deployed an ML model as a batch job, but that post was focused on
small scale batch jobs that could run quickly on single machines.

Because the results of a batch prediction job are stored and accessed
later by clients, the user can't interact with the model directly. This
means that the client that is using the predictions produced by the
model is not able to ask for predictions directly from the ML model
software component, and must access the data set produced by the batch
job to get predictions from the model.

# Package Structure

To begin, I set up the project structure for the job package:

```
-   data (data files used for testing the job)
-   model_map_reduce_job (python package for the map reduce job)
    -   __init__.py
    -   config.py
    -   ml_model_map_reduce_job.py
    -   ml_model_manager.py
-   tests ( unit tests )
-   Makefle
-   mrjob.conf (configuration file for MapReduce framework)
-   README.md
-   requirements.txt
-   setup.py
-   test_requirements.txt
```

This structure can be seen here in the [github
repository](https://github.com/schmidtbri/map-reduce-ml-model-deployment).

# Building MapReduce Jobs

A MapReduce job is made up of two basic steps: the map step and the
reduce step. Both steps are implemented as simple functions that receive
data, process it and return the results. The map step is responsible for
implementing filtering and sorting and the reduce step is responsible
for calculating aggregate results. The MapReduce system is responsible
for starting, managing, and stopping the code in the map and reduce
functions, for serializing and deserializing the data, and for managing
the redundancy and fault tolerance of the execution of the map and
reduce functions.

The MapReduce implementation provided by Hadoop is able to do data
processing with map and reduce functions implemented in many different
programming languages by using the [streaming
interface](https://hadoop.apache.org/docs/r1.2.1/streaming.html).
In this blog post, we'll use this interface to run a model prediction
job using Python. This simplifies the deployment of the model greatly,
since we don't need to rewrite the model's prediction code in order to
deploy it to a Hadoop cluster. We'll be using the [mrjob python
package](https://mrjob.readthedocs.io/en/latest/index.html)
to write the MapReduce job.

# Installing the Model

In order to write a MapReduce job that is able to handle any machine
learning model, we'll start by installing a model into the environment.
For this we can use the same model we've used before, the iris\_model
package. This package can be installed from a git repository with this
command:

```
pip install git+https://github.com/schmidtbri/ml-model-abc-improvements
```

Now that we have the model installed in the environment, we can try it
out by opening a python interpreter and entering this code:

```python
from iris_model.iris_predict import IrisModel
>>> model = IrisModel()
>>> model.predict({"sepal_length":1.1, "sepal_width": 1.2, "petal_width": 1.3, "petal_length": 1.4})
{'species': 'setosa'}
```

To load the model inside of the MapReduce job, we'll point at the
IrisModel class in a configuration file. The configuration file looks
like this:

```python
class Config(dict):
    models = [{
        "module_name": "iris_model.iris_predict",
        "class_name": "IrisModel"
    }]
```

The code above can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/model_mapreduce_job/config.py#L4-L12).

This configuration will be used by the job to dynamically load the model
packages. The module\_name and class\_name fields allow the job to
import the class that contains the implementation of the model's
prediction algorithm. The models list can contain pointers to many
models, so there are no limitations to how many models can be hosted by
the MapReduce job.

# Managing Models

As in previous blog posts, we'll use a singleton object to manage the ML
model objects that will be used to make predictions. The class that the
singleton object is instantiated from is called "ModelManager". The
class is responsible for instantiating MLModel objects, managing the
instances, returning information about the MLModel objects, and
returning references to the objects when needed. The code for the
ModelManager class can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/model_mapreduce_job/model_manager.py).
For a full explanation of the code in the class, read this [blog
post]({filename}/articles/using-ml-model-abc/post.md).

# MLModelMapReduceJob Class

We now have the model package installed and the ModelManager class to
manage it, so we can start to write the MapReduce job itself. The
MapReduce job is defined as a subclass of the MRJob base class which
defines map() and reduce() methods that implement the functionality of
the job. To start, we'll load the right configuration by accessing the
APP\_SETTINGS environment variable:

```python
configuration = __import__("model_mapreduce_job"). 
    __getattribute__("config").
    __getattribute__(os.environ["APP_SETTINGS"])
```

The code above can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/model_mapreduce_job/ml_model_map_reduce_job.py#L12-L15).

With the configuration loaded, we'll instantiate the ModelManager
singleton which will hold the references to the model objects that we
want to host in this MapReduce job:

```python
model_manager = ModelManager()
model_manager.load_models(Config.models)
```

The code above can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/model_mapreduce_job/ml_model_map_reduce_job.py#L17-L19).

By putting this initialization at the top of the module, we can be sure
that the models are initialized one time only, when the module is loaded
by the python interpreter.

Now we can write the class that makes up the MapReduce job:

```python
class MLModelMapReduceJob(MRJob):

    INPUT_PROTOCOL = JSONValueProtocol
    OUTPUT_PROTOCOL = JSONProtocol
    
    DIRS = ['../model_mapreduce_job']
```

The code above can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/model_mapreduce_job/ml_model_map_reduce_job.py#L22-L29).

The INPUT\_PROTOCOL and OUTPUT\_PROTOCOL class properties define the
input and output
[protocols](https://mrjob.readthedocs.io/en/latest/guides/writing-mrjobs.html#protocols)
of the MapReduce steps. A protocol is a piece of code that reads and
writes data to the filesystem, it is useful to abstract out the map and
reduce steps from the format in which the data is stored. The DIRS class
property tells the MrJob package that the code in this module depends on
code inside of the "model\_map\_reduce" directory, this causes MrJob to
copy the code whenever it creates a deployment package for this job.
These options help to simplify the code and deployment of the job.

The job class needs to be initialized, so we'll add a \_\_init\_\_()
method:

```python
def __init__(self, *args, **kwargs):
    super(MLModelMapReduceJob, self).__init__(*args, **kwargs)
    self._model = model_manager.get_model(self.options.model_qualified_name)
    
    if self._model is None:
        raise ValueError("'{}' not found in the ModelManager instance.".format(self.options.model_qualified_name))
```

The code above can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/model_mapreduce_job/ml_model_map_reduce_job.py#L31-L38).

The \_\_init\_\_ method first calls the MrJob base class' \_\_init\_\_
method so that it can do framework-level initialization. Next, we ask
the ModelManager singleton for an instance of the model that we want to
host in the MapReduce job. The qualified name of the model is accessed
from the self.options.model\_qualified\_name variable, which is set by a
command line option. Lastly, we check that a model object was actually
returned by the ModelManager and raise an exception if it wasn't.

Next, the MapReduce job must be able to run on any model that is inside
of the ModelManager instance. To support this, we will add a command
line option to the job that accepts the qualified name of the model we
want to run:

```python 
def configure_args(self):
    super(MLModelMapReduceJob, self).configure_args()

    self.add_passthru_arg('--model_qualified_name', \
        type=str, help='Qualified name of the model.')
```

The code above can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/model_mapreduce_job/ml_model_map_reduce_job.py#L40-L43).

This function allows us to extend the command line options already
supported by the MrJob framework. The command line argument passes
through the framework and is stored in the self.options object, which we
used in the code in the \_\_init\_\_ method to select the model we want
to use for the job.

Now that we have an initialized job class, we can write the code that
actually does the work of the MapReduce job. The mapper function looks
like this:

```python
def mapper(self, _, data):
    prediction = None

    try:
        prediction = self._model.predict(data=data)
    except Exception as e:
        prediction = None
    
    yield data, prediction
```

The code above can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/model_mapreduce_job/ml_model_map_reduce_job.py#L45-L55).

This function is very simple, it receives a dictionary in the "data"
argument, makes a prediction with the model, and returns a tuple of the
prediction input and output. The data argument is a dictionary because
we used the "JSONValueProtocol" as the INPUT\_PROTOCOL for this job.
This protocol deserializes a JSON string into a native Python object. By
using this protocol, we saved ourselves the trouble of having to
deserialize the input to JSON in the mapper step. If the model fails to
make a prediction, then None is returned as the prediction. The
OUTPUT\_PROTOCOL option is set to "JSONProtocol", which serializes the
key-value pair to two JSON strings separated by a tab character.

The output of the mapper step is always a key-value pair in which the
key must be unique across the inputs of the step. If any input is
repeated, the mapper step will make a prediction on it, but the
MapReduce framework will only return one result for the key to the next
step. This behavior sets up a limitation on our model: it must always
produce the same prediction given the same input, which is to say that
the model must make predictions deterministically. If the model is not
deterministic, the MapReduce framework will choose the first prediction
made for the input record. This may not matter in some situations but
may break any steps that use the results of this step if this behavior
is not handled correctly.

This MapReduce job does not need a reduce step since we only need to
make predictions and return the results. However, this job can be
combined with other MapReduce jobs that do use reduce steps to make more
a complex data processing pipeline.

# Testing the Job

Now that we have the code for the MapReduce job, we will test it locally
against a small data file. Because of the input and output protocol
options, the model is able to accept JSON files as input and it will
produce JSON files as output. Here is an example of the JSON that we
will feed to the job:

```json
{ "sepal_length": 5.0, "sepal_width": 3.2, "petal_length": 1.2, "petal_width": 0.2}
{ "sepal_length": 5.5, "sepal_width": 3.5, "petal_length": 1.3, "petal_width": 0.2}
...
```

The data file can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/data/input.ldjson).

To execute the job locally, these commands need to be run:

```bash
export PYTHONPATH=./
export APP_SETTINGS=ProdConfig
python model_mapreduce_job/ml_model_map_reduce_job.py \
  --model_qualified_name iris_model ./data/input.ldjson > data/output.ldjson
```

After the job runs, the output of the map step will be in the /data
folder. The input json string and resulting prediction will be on one
line of the file separated by a tab character. One input line had JSON
with a schema that the model could not accept, so the output should
contain a null prediction for that input. The \--model\_qualified\_name
command line argument tells the job to use the iris\_model model from
the ModelManager when running the job.

# Deploying to AWS

The mrjob package supports running jobs in the [AWS Elastic Map
Reduce](https://aws.amazon.com/emr/) (EMR) service. To run
the model job, we'll need an account in AWS. To interact with AWS, we'll
need to install the boto3 and awscli python packages:

```bash
pip install boto3 awscli
```

Next we'll configure the API access keys. A set of access keys can be
generated and configured by [following these
instructions](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html).
The configuration will look like this:

```bash
aws configure
AWS Access Key ID [*******************]: xxxxxxxxxxxxxxxxxx
AWS Secret Access Key [******************]:xxxxxxxxxxxxxxxxxxx
Default region name [us-east-2]: us-east-1
Default output format [None]:
```

In order to run the model job in AWS EMR, we'll first need to configure
a default role for the job to assume. A simple way to do this is already
supported in the AWS CLI tool. The command looks like this:

```bash
aws emr create-default-roles
```

In order to set up the execution environment in the nodes before we run
the model prediction code we'll need to execute a few commands. The
mrjob package supports this through a configuration file called
mrjob.conf. The config file is written in YAML and looks like this:

```yaml
runners:
  emr:
    bootstrap:
    - sudo yum update -y
    - sudo yum install git -y
    - sudo pip-3.6 install -r ./requirements.txt#
    setup:
    - export PYTHONPATH=$PYTHONPATH:model_mapreduce_job/#
    - export APP_SETTINGS=ProdConfig
```

The file can be found
[here](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/mrjob.conf).

The file is able to hold configuration for several types of runners, for
now we'll only configure the EMR runner. The bootstrap section holds
commands that will be executed one time, when the cluster node is first
created. In this section we're updating the yum package manager,
installing the git client, and installing all of the python dependencies
we need to run the model package from the
[requirements.txt](https://github.com/schmidtbri/map-reduce-ml-model-deployment/blob/master/requirements.txt)
file in the project.

The setup section holds commands that will be executed whenever the
MapReduce job starts up. In this section, we are setting up the
PYTHONPATH environment variable that the python interpreter will need in
order to find the code files that make up the job. We are also setting
the APP\_SETTINGS environment variable that tells the job which
environment it is running in, for now we're running the job with the
ProdConfiguration settings.

Now that we have the credentials and configuration set up, we can run
the job in AWS. The command looks like this:

```bash
python model_mapreduce_job/ml_model_map_reduce_job.py \
  --conf-path=./mrjob.conf -r emr --iam-service-role EMR_DefaultRole \ 
  --model_qualified_name iris_model ./data/input.ldjson
```

The mrjob package will create an S3 bucket for the job, upload the code
and data to the S3 bucket, create an EMR cluster for the job, and run
the job. The results of the job will be stored into the same S3 bucket.

# Closing

By using the MapReduce framework, we are able to make a large number of
predictions on a cluster of computers. Because of the simple design of
the MapReduce framework, a lot of the complexities of running a job on
many computers are abstracted out. This deployment option for machine
learning models enables us to deploy model prediction jobs against truly
massive data sets.

By building the prediction job so that it uses the MLModel interface,
the deployment of a model as a MapReduce job is greatly simplified. The
MapReduce job that we built in this blog post is able to host any
machine learning model that uses the MLModel interface which makes the
code highly reusable. Once again, the MLModel interface allowed us to
abstract out the complexities of building a machine learning model from
the complexities of deploying a machine learning model.

One of the drawbacks of the implementation is the fact that it only
accepts LDJSON encoded files as input to the job. This is for the sake
of simplicity, since having the field names along with the data makes
the code easier to understand. An improvement to the code would be to
enable other protocols so that we can use other file types with the job.
Furthermore, it would be easy to make the choice of input and output
protocols a command line option that can be chosen at execution time.

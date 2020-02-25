# MapReduce ML Model Deployment
Deploying an ML model in a MapReduce job.


![](https://github.com/schmidtbri/map-reduce-ml-model-deployment/workflows/Build/badge.svg)

Deploying an ML model in a MapReduce job.

This code is used in this [blog post](https://medium.com/@brianschmidt_78145/a-mapreduce-ml-model-deployment-98a2b7de5803).

## Installation 
The makefile included with this project contains targets that help to automate several tasks.

To download the source code execute this command:

```bash
git clone https://github.com/schmidtbri/map-reduce-ml-model-deployment
```

Then create a virtual environment and activate it:

```bash
# go into the project directory
cd map-reduce-ml-model-deployment

make venv

source venv/bin/activate
```

Install the dependencies:

```bash
make dependencies
```

## Running the unit tests
To run the unit test suite execute these commands:
```bash

# first install the test dependencies
make test-dependencies

# run the test suite
make test
```

## Running the Job
To start the job execute these commands:
```bash
export PYTHONPATH=./
export APP_SETTINGS=ProdConfig
python model_mapreduce_job/ml_model_map_reduce_job.py \
    --model_qualified_name iris_model ./data/input.ldjson > \
    data/output.ldjson
```

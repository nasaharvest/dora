# DORA Experiment Pipeline #

## Introduction ## 
The DORA Experiment Pipeline is the codebase to conduct experiments for the 
Earth Science, Astrophysics, and Planetary Science use cases of the DORA 
project. 

The DORA Experiment Pipeline is developed and tested using Python 3.8.2, 
although the codebase should support Python 3.6+. The DORA Experiment Pipeline 
consists of the Data Loading, Feature Extraction, Outlier Ranking, and Results 
Organization modules. 

## Installation ## 
The DORA Experiment Pipeline provides a `setup.py` file for installing the DORA 
Experiment Pipeline itself and all the dependencies it requires. Note that the 
DORA Experiment Pipeline has already been installed on MLIA machines (e.g., 
analysis, paralysis, mlia-compute1, etc.) at `/proj/dora/dora-venv` , and can be 
invoked using the following command 

```
source /proj/dora/dora-venv/bin/activate
```

Please following the following steps to install the DORA Experiment Pipeline and 
all the required dependencies:

1. Clone the DORA github repository

```
git clone https://github.com/nasaharvest/dora.git
```

2. Install the DORA Experiment Pipeline and all the required dependencies

```
cd /PATH/TO/THE/ROOT/DIR/OF/DORA/GITHUB/REPOSITORY/

# This command needs to be executed in the DORA root dir that contains setup.py
pip install .
```

3. Verify the installation is successful

```
python

>>> import dora_exp_pipeline
>>> dora_exp_pipeline.__version__
'0.0.1'
```

## Usage ##
The entry point of the DORA Experiment Pipeline is the `dora_exp.py` script. 
After the installation of the DORA Experiment Pipeline, `dora_exp.py` script 
will be installed as a command line program `dora_exp`, which should be 
available globally in your python environment. To see its usage, run the 
following command: 

```
dora_exp -h
``` 

Then you should see the arguments as below:

```
usage: dora_exp [-h] [-l LOG_FILE] [--seed SEED] config_file

The DORA Experiment Pipeline

positional arguments:
  config_file           Path to the configuration file

optional arguments:
  -h, --help            show this help message and exit
  -l LOG_FILE, --log_file LOG_FILE
                        Log file. This is optional. If enabled, a log file will 
                        be saved.
  --seed SEED           Integer used to seed the random generator for the DORA 
                        experiment pipeline. Default is 1234.
``` 

Use the following command to invoke the `dora_exp` program:

```
dora_exp config.yml
```

(TODO: Add a section in the README for config file. For now, please see the 
example config files in `dora_exp_pipeline/example_config/`.)

It may be inconvenient to run `dora_exp` program when you are in the development 
mode because it requires to constantly re-install `dora_exp` whenever a change 
is made in the `dora_exp.py` script. The `dora_exp` program is installed from 
the `dora_exp.py` script, which means we can still run `dora_exp.py` as a 
regular python script independent to the installed `dora_exp` program. To run 
`dora_exp.py` as a regular python script:

```
cd /PATH/TO/DORA/GIT/dora/dora_exp_pipeline/
python dora_exp.py config.yml
```

Note that running `dora_exp.py` as a python script is only recommended for 
development. Please follow the instructions in the Installation section to 
properly install `dora_exp` once the development is complete.  
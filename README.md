# BeaconTau

## Introduction

A BEACON data analysis package for python3.

This package uses [pybind11](https://github.com/pybind/pybind11) to get the raw c-structs from [the BEACON c-library](https://github.com/beaconTau/libbeacon) into python.
This package calls the c backend to read binary data from disk into your python prompt.
From there all the standard python loveliness is available.

The current functionality is somewhat basic, the most glaring issue is that currently only the gzipped data files can be parsed by the RunReader.

## Pre-requisites
1. python3
   - The recommended way to get it is via miniconda or anaconda if disk space and bandwidth aren't a concern. 
	 - You can find a suite of miniconda installers [here](https://repo.continuum.io/miniconda/).
   - A recent Vanilla python3 should also work fine though.

2. A recent c++ compiler
   - [pybind11](https://github.com/pybind/pybind11) requires a c++11 compiler (clue is in the name).
   - Unless you're on a very old machine you probably don't need to worry about this

## Installation

Here are two installation methods.
The only significant difference between them is that one requires you to choose (and need to remember) where you put your python environment.
For that reason I'm recommending the first of the two, installing via conda (then pip).

### 1. From PyPI with anaconda (or miniconda) *Recommended*
Make sure you have an anaconda3 or miniconda3 installation.
You can get a miniconda installation for you architecture [here](https://repo.continuum.io/miniconda/).

First create an environment for your BeaconTau to live in, for the sake of these instructions I'm calling it Beacon.

```bash
conda create Beacon
```

Then make sure you have pip installed (you may as well let it upgrade itself to the latest and greatest version)
```bash
conda install pip
pip install --upgrade pip
```

Finally, install BeaconTau
```bash
pip  install BeaconTau
```

Then, fire up python and you're good to go.
```python
import BeaconTau
```

Note that for future sessions you will need to do `conda activate Beacon` before starting python to have access to all the BeaconTau goodies.


### 2. From PyPI without anaconda (in a virtualenv)
Similar-ish to the adaconda method.
First, navigate to the directory you want to do some BEACON analysis in.
Then create a virtual environment, for the sake of these instructions I'm calling BeaconEnv.

```bash
python3 -m venv BeaconTau-env # Creates a virtual environment (you need only do this once)
source BeaconTau-env/bin/activate # Load the virtual environment (do this once per terminal session)
pip install BeaconTau # Install from PyPI (only need to do this once, unless upgrading)
```
From there start `python`

```python
import BeaconTau
```
And you should be good to go.
Remember that you will need to do `source BeaconTau-env/bin/activate` each time you want to use this python module!



## Flame (Facility for Live Action Monitoring of Events)

A prototype online browser based event on BeaconTau and bokeh.

## Version history

I'm aiming to keep [libbeacon](https://github.com/beaconTau/libbeacon) version tags in sync with BeaconTau version tags.

| Version | Notes                                                                                             |
|---------|---------------------------------------------------------------------------------------------------|
| 0.1.0   | Working local implementation of BeaconTau and Flame                                               |
| 0.1.1   | First working version on PyPI!                                                                    |
| 0.1.2   | Bug fix release: for pip install process, make sure pybind11 is installed before running setup.py |
| 0.1.3   | Bug fix release: for pip install process, set std=c++11 for compiling against pybind              |
| 0.1.4   | Track upstream changes, from libnuphase -> libbeacon                                              |






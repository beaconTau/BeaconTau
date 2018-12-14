# BeaconTau

## Introduction

A BEACON data analysis package for python3.

This package uses [pybind11](https://github.com/pybind/pybind11) to get the raw c-structs from [the BEACON c-library](https://github.com/beaconTau/libbeacon) into python.
This package calls the c backend to read binary data from disk into your python prompt.
From there all the standard python loveliness is available.

## Quick start
Once you've installed the package (see below) define an environment variable called `BEACON_DATA_DIR` with the directory containing all the BEACON runs (and the hk folder).
From your python prompt.
```python
>>> import BeaconTau as bt
>>> dd = bt.DataDirectory()      # Will look in BEACON_DATA_DIR
>>> r = dd.run(99)               # to get run 99, if you have it
>>> r.draw('trigger_thresholds')  # *limited* ROOT-style draw functionality is available, emphasis on limited
>>> e = r.get_entry(0)           # You can access events by entry (index) where 0 is the first event in the run...
>>> e = r.get_event(99000000002) # or by the full event number (provided it is in the run)
>>> e.plot()                     # Quickly plot them in the time domain
>>> e.plot(freq_domain = True)   # Or the frequency domain
>>> e.channel(3)                 # Gives you the actual waveforms,
>>> e.channel_psd(3)             # gives you the power spectrum...
```
Take a look at the actual source code to see more.
Happy analyzing!

## Pre-requisites
1. python3
   - The recommended way to get it is via miniconda or anaconda if disk space and bandwidth aren't a concern. 
	 - You can find a suite of miniconda installers [here](https://repo.continuum.io/miniconda/).
   - A recent "vanilla" python3 installation should also work fine though.

2. A recent c++ compiler
   - [pybind11](https://github.com/pybind/pybind11) requires a c++11 compiler (clue is in the name).
   - Unless you're on a very old machine you probably don't need to worry about this, otherwise install more recent c++ compiler and check it is invoked by default.

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

Finally, install BeaconTau (sadly the name Beacon was already taken)
```bash
pip  install BeaconTau
```

Then, fire up python and you're good to go.
```python
>>> import BeaconTau
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
>>> import BeaconTau
```
And you should be good to go.
Remember that you will need to do `source BeaconTau-env/bin/activate` each time you want to use this python module!

## To use with Jupyter Notebooks:
In addition to installing BeaconTau, you need to build an ipython kernel that you can load in a Jupyter Notebook. The example below installs a ipython kernel based on your conda install "Beacon" and  accesible in jupyter as "Python (Beacon)"

source activate Beacon
conda install ipykernel 
python -m ipykernel install --user --name Beacon --display-name "Python (Beacon)"


## Version history

See [RELEASES.md](https://github.com/beaconTau/BeaconTau/blob/master/RELEASES.md).

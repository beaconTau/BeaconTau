# BeaconTau

A BEACON data analysis package for python3.

This package uses [pybind11](https://github.com/pybind/pybind11) to get the raw c-structs from [the BEACON fork of libnuphase](https://github.com/beaconTau/libnuphase) into python.
From there all the standard python loveliness is available.

The current functionality is somewhat basic, the most glaring issue is that currently only the gzipped data files can be parsed by the RunReader.

## Installation



### From PyPI in a virtualenv

Navigate to the directory you want to do some BEACON analysis in.
Do
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



### From PyPI with Anaconda
**Warning: this method is as yet untested! Hopefully some more detailed documentation will arrive soon.***
Following [these instructions](https://conda.io/docs/user-guide/tasks/manage-pkgs.html#installing-non-conda-packages).
Make sure pip is installed in your current conda environment `conda install pip`.
From there:

```bash
source activate BeaconTau-env # or whatever environment you desire
pip install BeaconTau
```



## Flame (Facility for Live Action Monitoring of Events)

A prototype online browser based event on BeaconTau and bokeh.

## Version history

I'm aiming to keep [libnuphase](https://github.com/beaconTau/libnuphase) version tags in sync with BeaconTau version tags.

| Version | Notes                                               |
|---------|-----------------------------------------------------|
| 0.1.0   | Working local implementation of BeaconTau and Flame |
| 0.1.1   | First working version on PyPI!                      |





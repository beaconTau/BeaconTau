# BeaconTau

A BEACON data analysis package for python3.

This package uses [pybind11](https://github.com/pybind/pybind11) to get the raw c-structs from [the BEACON fork of libnuphase](https://github.com/beaconTau/libnuphase) into python.
From there all the standard python loveliness is available.

## Installation

### From PyPI

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


## Flame (Facility for Live Action Monitoring of Events)

A prototype online browser based event on BeaconTau and bokeh.

## Version history

I'm aiming to keep [libnuphase](https://github.com/beaconTau/libnuphase) version tags in sync with BeaconTau version tags.

| Version | Notes                                               |
|---------|-----------------------------------------------------|
| 0.1.0   | Working local implementation of BeaconTau and Flame |
| 0.1.1   | First working version on PyPI!                      |





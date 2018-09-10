from _BeaconTau import * # Load the pybind11 stuff defined in _BeaconTau as if it's in BeaconTau

from .EventAnalyzer import EventAnalyzer
from .RunAnalyzer import RunAnalyzer
from .DataDirectory import DataDirectory

name = "BeaconTau"

def main():
    dd = DataDirectory()

    for run in dd:
        for entry in range(2):
            event = run.get_entry(entry)
            event.plot()
        run.draw('trigger_thresholds')

if __name__ == '__main__':
    main()


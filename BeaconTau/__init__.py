from _BeaconTau import * # Load the pybind11 stuff defined in _BeaconTau as if it's in BeaconTau

from .EventAnalyzer import EventAnalyzer
from .RunAnalyzer import RunAnalyzer
from .DataDirectory import DataDirectory

name = "BeaconTau"

def main():
    d = DataDirectory()

    for r in d:
        for entry in range(2):
            e = r.get_entry(entry)
            e.plot()
        r.draw('trigger_thresholds')

# plt.ion()
# plt.show()
if __name__ == '__main__':
    main()


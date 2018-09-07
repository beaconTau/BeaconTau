from _BeaconTau import * # This imports the c++ defined code from BeaconTau.cpp
import os
from .RunAnalyzer import RunAnalyzer


class DataDirectory():
    """
    High level interface to the BEACON data directory structures.
    Allows iteration of RunAnalyzers over all runs in the directory

    First looks in an optional data_dir string.
    If one is not provided, then it looks for a BEACON_DATA_DIR environment variable.
    If there isn't one it looks in the current directory.
    If it doesn't find any run subfolders in any of those places, it gives up.
    """
    def __init__(self, data_dir = None):

        self.data_dir = data_dir

        if self.data_dir == None:
            try:
                self.data_dir = os.environ['BEACON_DATA_DIR']
                print('Found ' + self.data_dir + ' from BEACON_DATA_DIR')
            except:
                print('No BEACON_DATA_DIR environment variable, setting to current directory')
                self.data_dir = os.getcwd()

        self.run_dirs = [d for d in os.listdir(self.data_dir) if 'run' in d]

        if len(self.run_dirs) == 0:
            raise ValueError("Couldn't find any runs under " + self.data_dir)

        self.runs = sorted([int(x.strip('run')) for x in self.run_dirs])
        self._i =  0

    def __repr__(self):
        return '<BeaconTau.DataDirectory at ' + str(self.data_dir) + ' containing runs ' + str(self.runs) + '>'

    def __iter__(self):
        return self

    def __next__(self):
        if self._i < len(self.runs):
            self._i += 1 # For next call to __next__
            return RunAnalyzer(self.runs[self._i - 1], self.data_dir)
        else:
            raise StopIteration

    def run(self, run_number):
        run_index = -1
        try:
            run_index = self.runs.index(run_number)
        except:
            raise ValueError('No run ' +  str(run_number) + ' in ' + self.data_dir + ', available runs are ' + str(self.runs))

        return RunAnalyzer(run_number, self.data_dir)

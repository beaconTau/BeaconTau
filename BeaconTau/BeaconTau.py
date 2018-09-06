from _BeaconTau import * # This imports the c++ defined code from BeaconTau.cpp
import matplotlib.pyplot as plt
from scipy import signal
import os
from math import floor, log10

class EventAnalyzer():
    """
    Do some useful things with the raw Event and Header classes defined in BeaconTau.cpp
    The magic of pybind11 only gets us so far: it's hard to extend the same c++ classes in python.
    Inheritance is also pain to implement (and would be inefficient to copy data to the derived class).
    So instead this we have this EventAnalyzer class that has the event and header as members, and does useful things with them.
    """

    def __init__(self, header, event):
        if header.event_number != event.event_number:
            raise ValueError('Mismatched header and event!')
        self.header = header
        self.event = event

        self.time_array = None # Constructed on demand
        self.freq_array = None # Constructed on demand
        self.dt = 2.0 # Nano seconds
        self.df = 1e3/(self.event.buffer_length*self.dt) # 1e3 GHz -> MHz


    def __repr__(self):
        return '<BeaconTau.EventAnalyzer for event ' + str(self.event.event_number) + '>'

    def channel(self, chan_index, board_index = 0):
        # The primary method of accessing the channel data.
        # Automatically trims the buffer to the correct length.
        return self.event.data[board_index][chan_index][:self.event.buffer_length]

    def channel_psd(self, chan_index, board_index = 0):
        freqs, psd = signal.periodogram(self.channel(chan_index), self.df)
        return psd

    def channel_psd_db(self, chan_index, board_index = 0):
        psd = self.channel_psd(chan_index, board_index = board_index)
        psd_db = [log10(p) if p > 0 else 0 for p in psd]
        return psd_db

    def times(self):
        # Dynamically constructs the time array for the event
        if self.time_array is None:
            self.time_array = [self.dt*i for i in range(self.event.buffer_length)]
        return self.time_array

    def freqs(self):
        if self.freq_array is None:
            nf = floor(self.event.buffer_length/2) + 1
            self.freq_array = [self.df*j for j in range(nf)]
        return self.freq_array

    def plot(self, n_rows = 2, show = False, axes = None, freq_domain = False, log_scale = True):
        # Draw the event in Matplotlib
        for board in self.event.data:
            n_cols = int(len(board)/n_rows)

            # TODO add check on axes length if extenal set of axes passed in
            # TODO for multiple boards, maybe that's overkill...
            if axes is None:
                fig, axes = plt.subplots(n_rows, n_cols, sharey = True, sharex = True)
                mng = plt.get_current_fig_manager()
                mng.resize(*mng.window.maxsize())
            for chan in range(len(board)):
                axes.flat[chan].set_title('Channel ' + str(chan+1))
                color = 'C' + str(chan) # matplotlib accepts strings beginning with a capital C for colors
                if freq_domain is False:
                    axes.flat[chan].plot(self.times(),  self.channel(chan), color)
                    axes.flat[chan].set_xlabel('Time (ns)')
                    axes.flat[chan].set_ylabel('Amplitude (mV)')
                else:
                    axes.flat[chan].set_xlabel('Freq (MHz)')
                    if log_scale is True:
                        axes.flat[chan].plot(self.freqs(), self.channel_psd_db(chan), color)
                        axes.flat[chan].set_ylabel('PSD (dB)')
                    else:
                        axes.flat[chan].plot(self.freqs(), self.channel_psd(chan), color)
                        axes.flat[chan].set_ylabel('PSD (mV^{2} / MHz)')
            plt.suptitle('Event ' + str(self.event.event_number))
        if show is True:
            plt.show()

class RunAnalyzer():
    """
    Class for examining data in a run.
    Can plot/scan any attribute in the Status/Header/Event files.
    Can pull up individual events by event_number or entry.
    Wraps the file reading action from FileReader into something a bit more python friendly.
    """
    def __init__(self, run, data_dir):
        self.run = run
        self.run_reader = FileReader(run, data_dir)
        self.extracted_values = dict()

    def split_attribute(self, attribute):
        attributes = attribute.split(':')
        return attributes

    def cached_extract(self, attribute):
        if attribute in self.extracted_values:
            return self.extracted_values[attribute]
        else:
            values = self.extract(attribute)
            if values is not None:
                self.extracted_values[attribute] = values
            return values

    def extract(self, attribute):

        values = None
        try:
            values = [e.__getattribute__(attribute) for e in self.run_reader.events]
        except:
            try:
                values = [h.__getattribute__(attribute) for h in self.run_reader.headers]
            except:
                try:
                    values = [s.__getattribute__(attribute) for s in self.run_reader.statuses]
                except:
                    raise ValueError(attribute + ' is not something in BeaconTau.Status, BeaconTau.Header, or BeaconTau.Event!')

        return values

    def draw(self, attribute, show = False):
        values = self.cached_extract(attribute)
        if values is not None:
            fig = plt.figure()
            mng = plt.get_current_fig_manager()
            mng.resize(*mng.window.maxsize())
            plt.xlabel('Entry')
            plt.ylabel(attribute)
            plt.title('Run ' + str(self.run))
            lines = plt.plot(values)
            labels = [attribute + '[' + str(c) + ']' for c in range(len(lines))]
            plt.legend(lines, labels)
            if show is True:
                plt.show()
            return fig

    def scan(self, attribute):
        values = self.cached_extract(attribute)
        if values is not None:
            entries = 0
            for entry, value in enumerate(values):
                to_print = str(entry) + '\t' + str(value)
                print(to_print)
                entries += 1            
                if entry > 0 and (entry+1) % 25 == 0:
                    keys = input('Press q to quit: ')
                    if len(keys) > 0 and keys[0] == 'q':
                        break
            print('Finished scanning ' + str(entries) + ' entries')


    def get_entry(self, entry):
        return EventAnalyzer(self.run_reader.headers[entry],  self.run_reader.events[entry])

    def get_event(self, event_number):
        event_numbers = self.cached_extract('event_number')
        try:
            entry = event_numbers.index(event_number)
            return get_entry(entry)
        except:
            raise ValueError(str(event_number) + ' not found in run ' + str(self.run))
            return None


class DataDirectory():
    """
    High level interface to the BEACON data directory structures.
    Allows iteration over runs.

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
        return '<BeaconTau.DataDirectory containing runs' + str(self.runs) + '>'

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

def main():
    d = DataDirectory()

    for r in d:
        for entry in range(2):
            e = r.get_entry(entry)
            e.plot()
        r.draw('trigger_thresholds')

plt.ion()
plt.show()
if __name__ == '__main__':
    main()


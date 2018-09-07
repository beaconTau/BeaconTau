from _BeaconTau import * # This imports the c++ defined code from BeaconTau.cpp
from .EventAnalyzer import EventAnalyzer
import matplotlib.pyplot as plt

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

    def __repr__(self):
        return ('<BeaconTau.RunAnalyzer for run ' + str(self.run) + '>')

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
            values = [s.__getattribute__(attribute) for s in self.run_reader.statuses]
            return values
        except:
            pass
        try:
            values = [h.__getattribute__(attribute) for h in self.run_reader.headers]
            return values
        except:
            pass
        try:
            values = [e.__getattribute__(attribute) for e in self.run_reader.events]
            return values
        except:
            pass

        raise AttributeError(attribute + ' is not something in BeaconTau.Status, BeaconTau.Header, or BeaconTau.Event!')
        return None

    def draw(self, attribute, show = False):
        plt.ion()
        plt.show()
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

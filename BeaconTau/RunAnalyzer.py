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
        self.file_reader = FileReader(run, data_dir)
        self._get_cache = {}

        self._attributes = {}
        for c in [Status, Header, Event]:
            # Here we sort the list of strings in order from longest to shortest
            self._attributes[c.__name__] = sorted([a for a in vars(c) if '__' not in a], key=len, reverse=True)
        #print(self._attributes)

    def __repr__(self):
        return ('<BeaconTau.RunAnalyzer for run ' + str(self.run) + '>')


    def _substitute(self, code: str, matches):
        for c, attrs in self._attributes.items():
            for a in attrs:
                if a in code:
                    sub_codes = code.split(a, 1)
                    new_code = sub_codes[0] + '{'  + str(len(matches)) + '}'+ sub_codes[1]
                    matches.append(a)
                    return new_code, matches
        return code, matches

    def _split_expressions(self, code:str):
        return code.split(':')

    def _get_one(self, code: str):

        var_list = []
        while True:
            new_code, var_list = self._substitute(code, var_list)
            if new_code == code:
                break
            else:
                code = new_code

        attributes = []
        for var in var_list:
            attributes.append(self.get_attribute(var))

        subs = ['{' + str(i) + '}' for i in range(len(attributes))]

        results = []

        if len(attributes) > 0:
            for vals in zip(*attributes):
                #print(vals)
                entry_code = code
                for i, val in enumerate(vals):
                    entry_code = entry_code.replace(subs[i], str(val))
                result = eval(entry_code)
                results.append(result)

        else: # Then this expression is actually a constant
            results = [eval(code)]* len(self.file_reader.headers)
            
        return results

    def get(self, expression: str):
        codes = self._split_expressions(expression)
        values = [self._get_one(code) for code in codes]
        return values, codes

    def get_attribute(self, attribute):

        values = None

        # first try the cache
        if attribute in self._get_cache:
            values = self._get_cache[attribute]

        if values is None:
            if attribute in self._attributes['Status']:
                values = [s.__getattribute__(attribute) for s in self.file_reader.statuses]
            elif attribute in self._attributes['Header']:
                values = [h.__getattribute__(attribute) for h in self.file_reader.headers]
            elif attribute in self._attributes['Event']:
                values = [e.__getattribute__(attribute) for e in self.file_reader.events]

        # Add it to the cache if we have it
        if values is not None:
            self._get_cache[attribute] = values
        # Otherwise, we complain
        else:
            raise AttributeError(attribute + ' is not something in BeaconTau.Status, BeaconTau.Header, or BeaconTau.Event!')

        return values

    def draw(self, expression, option = None, bins = None, range = None):
        plt.ion()
        plt.show()
        values, names = self.get(expression)

        ax = plt.gca()

        h = None
        if len(values) == 1:
            # 1D histogram
            h = plt.hist(values, bins = bins, range = range)            
            ax.set_xlabel(names[0])
        
        if len(values) == 2:
            if option == 'col':
                h = plt.hist2d(values[0], values[1], bins = bins, range = range)
            elif option == 'line':
                h = plt.plot(values[0], values[1])
            else:
                h = plt.scatter(values[0], values[1])

            ax.set_xlabel(names[0])
            ax.set_ylabel(names[1])
        if len(values) >= 3:
            colorable = None
            if 'col' in option:                
                h = plt.hist2d(values[0], values[1], weights = values[2])
                if 'z' in option:
                    colorable = h[3]
            else:
                h = plt.scatter(values[0], values[1], c = values[2])
                if 'z' in option:
                    colorable = h
            if colorable is not None:
                cbar = plt.gcf().colorbar(colorable)
                cbar.set_label(names[2])
                
            ax.set_xlabel(names[0])
            ax.set_ylabel(names[1])
        ax.set_title(expression)
        return h
    
    def scan(self, expression):
        values = self.get(expression)
        entries = 0
        print('Entry\t' + expression.replace(':', '\t'))
        for entry, vals in enumerate(zip(*values)):
            to_print = str(entry)
            for val in vals:
                to_print =  to_print + '\t' + str(val)
            print(to_print)
            entries += 1
            if entry > 0 and (entry+1) % 25 == 0:
                keys = input('Press q to quit: ')
                if len(keys) > 0 and keys[0] == 'q':
                    break
        print('Finished scanning ' + str(entries) + ' entries')

    def events(self):
        for entry in range(len(self.file_reader.headers)):
            yield self.get_entry(entry)

    def get_entry(self, entry):
        return EventAnalyzer(self.file_reader.headers[entry],  self.file_reader.events[entry])

    def get_event(self, event_number):
        event_numbers = self.get('event_number')
        try:
            entry = event_numbers.index(event_number)
            return self.get_entry(entry)
        except:
            raise ValueError(str(event_number) + ' not found in run ' + str(self.run))
            return None

from BeaconTau import NUM_BEAMS
from .DataDirectory import DataDirectory
from .RunAnalyzer import RunAnalyzer
from matplotlib import pyplot as plt
from matplotlib import animation as animate

from matplotlib.widgets import Button, TextBox, RadioButtons

from enum import Enum

class Domain(Enum):
    Time = 0
    Freq = 1


class Viewer():
    """
    A class for looking at BEACON events.

    Keybindings
       space : play/pause
       right : next event
       left  : previous event
       up    : go 1000 events forward
       down  : go 1000 events back
       d     : switch time/freq domain
       j     : jump to event
    """
    def __init__(self, run = None, data_dir = None):
        self.dd = DataDirectory(data_dir)

        self.run = None
        if run is None:
            run = self.dd.runs[-1] # Get the most recent

        self.n_rows = 2

        self.domain = Domain.Time
        self.log_scale = True #False

        self.fig = None
        self.axes = None
        self.lines = {}

        self.next_button = None
        self.prev_button = None
        self.play_button = None
        self.stop_button = None
        self.select_button = None
        self.timer = None
        self.playing = False

        self.run_selection = None
        self.entry_selection = None
        self.event_selection = None
        self.domain_selection = None
        self.trigger_beam_texts = None
        self.event_selector = None

        plt.ion()
        plt.show()

        self.set_run(run)

    def __del__(self):
        if self.timer is not None and self.playing is True:
            self.timer.stop()

    def forward(self, event):
        self.entry = self.entry + 1
        self.event_analyzer = self.run_analyzer.get_entry(self.entry)
        self.update()

    def backward(self, event):
        self.entry = self.entry - 1
        self.event_analyzer = self.run_analyzer.get_entry(self.entry)
        self.update()

    def start_play(self, event):
        self.playing = True
        if self.timer is None:
            self.timer = self.fig.canvas.new_timer(1)
            self.timer.add_callback(self.forward, None)
        self.timer.start()

    def stop_play(self, event):
        self.playing = False
        if self.timer is not None:
            self.timer.stop()

    def switch_domain(self, domain_str: str):
        if domain_str is 'Time':
            if self.domain is not Domain.Time:
                self.domain = Domain.Time
                self.update()

        elif domain_str is 'Freq':
            if self.domain is not Domain.Freq:
                self.domain = Domain.Freq
                self.update()
        else:
            raise ValueError('Unknown domain')

    def set_run(self, run: int):
        run = int(run)
        if run is not self.run:
            if run not in self.dd.runs:
                raise ValueError('No run ' + str(run) + ' in ' + str(self.dd))

            self.run = run
            self.run_analyzer = self.dd.run(self.run)
            self.entry = 0
            self.event_analyzer = self.run_analyzer.get_entry(self.entry)
            self.update()


    def set_entry(self, entry: int):
        entry = int(entry)
        if entry is not self.entry:
            self.entry = entry
            self.event_analyzer = self.run_analyzer.get_entry(self.entry)
            self.update()


    def set_event(self, event_number: int):
        event_number = int(event_number)
        event_numbers = self.run_analyzer.get('event_number')[0][0] # Is that right???
        entry = event_numbers.index(event_number)
        self.set_entry(entry)

    def __repr__(self):
        return '<BeaconTau.Viewer run ' + str(self.run) + ' event ' + str(self.event_analyzer.header.event_number) + '>'

    def update_header_text(self):
        if self.trigger_beam_texts is None:
            self.trigger_beam_texts = {}
            for beam in range(NUM_BEAMS):
                height = 0.03
                x = 0.93
                y = 0.84 - (beam+1)*height
                self.trigger_beam_texts[beam] = plt.figtext(x, y, 'Beam ' + str(beam).zfill(2), bbox=dict(facecolor='white'))

        for beam in range(NUM_BEAMS):
            if self.event_analyzer.beam_triggered(beam):
                self.trigger_beam_texts[beam].set_backgroundcolor('red')
            else:
                self.trigger_beam_texts[beam].set_backgroundcolor('white')

    def update(self):
        #plt.ioff()

        for b, board in enumerate(self.event_analyzer.event.data):
            if self.axes is None:
                n_cols = int(len(board)/self.n_rows)
                self.fig, self.axes = plt.subplots(self.n_rows, n_cols, sharey = True, sharex = True)

                #mpl.rcParams['keymap.back'].remove('left')
                #mpl.rcParams['keymap.forward'].remove('right')
                self.fig.canvas.mpl_connect('key_press_event', self.handle_keys)


                mng = plt.get_current_fig_manager()
                mng.resize(*mng.window.maxsize())
                for a, ax in enumerate(self.axes.flat):
                    color = 'C' + str(a) # matplotlib accepts strings beginning with a capital C for colors
                    self.lines[(b, a)], = ax.plot([], [], color)
                    ax.autoscale_view()
                    #print(self.lines[(b, a)])
                plt.ion()
                plt.show()

            for chan in range(len(board)):
                self.axes.flat[chan].set_title('Channel ' + str(chan+1))
                #self.axes.flat[chan].clear()
                if self.domain is Domain.Time:
                    #self.axes.flat[chan].plot(self.event_analyzer.times(),  self.event_analyzer.channel(chan), color)
                    self.lines[(b,chan)].set_data(self.event_analyzer.times(),  self.event_analyzer.channel(chan))
                    self.axes.flat[chan].set_xlabel('Time (ns)')
                    self.axes.flat[chan].set_ylabel('Amplitude (ADC)')
                else:
                    self.axes.flat[chan].set_xlabel('Freq (MHz)')
                    if self.log_scale is True:
                        self.lines[(b,chan)].set_data(self.event_analyzer.freqs()[1:],  self.event_analyzer.channel_psd_db(chan)[1:])
                        #self.axes.flat[chan].plot(self.event_analyzer.freqs()[1:], self.event_analyzer.channel_psd_db(chan)[1:], color)
                        self.axes.flat[chan].set_ylabel('PSD (dB)')
                    else:
                        self.lines[(b,chan)].set_data(self.event_analyzer.freqs[1:],  self.event_analyzer.channel_psd(chan)[1:])
                        #self.axes.flat[chan].plot(self.event_analyzer.freqs()[1:], self.event_analyzer.channel_psd(chan)[1:], color)
                        self.axes.flat[chan].set_ylabel('PSD (mV**2 / MHz)')
                self.axes.flat[chan].relim()
                self.axes.flat[chan].autoscale_view(True,True,True)

        plt.figure(self.fig.number)
        plt.suptitle('Run ' + str(self.run) + ' Event ' + str(self.event_analyzer.event.event_number))
        plt.show()
        self.update_header_text()

        hover_color = 'white'
        # For these btton axes the list is [left, bottom, width, height]
        if self.play_button is None:
            play_ax = plt.axes([0.9, 0.97, 0.05, 0.03])
            self.play_button = Button(play_ax, 'Play', hovercolor='green', color='lightgreen')
            self.play_button.on_clicked(self.start_play)

        if self.stop_button is None:
            stop_ax = plt.axes([0.95, 0.97, 0.05, 0.03])
            self.stop_button = Button(stop_ax, 'Stop', hovercolor='darkred', color='red')
            self.stop_button.on_clicked(self.stop_play)

        if self.next_button is None:
            next_ax = plt.axes([0.9, 0.94, 0.05, 0.03])
            self.next_button = Button(next_ax, 'Next', hovercolor='blue', color='lightblue')
            self.next_button.on_clicked(self.forward)

        if self.prev_button is None:
            prev_ax = plt.axes([0.95, 0.94, 0.05, 0.03])
            self.prev_button = Button(prev_ax, 'Prev', hovercolor='yellow', color='lightyellow')
            self.prev_button.on_clicked(self.backward)

        if self.select_button is None:
            select_ax = plt.axes([0.9, 0.91, 0.1, 0.03])
            self.select_button = Button(select_ax, 'Jump to event', hovercolor='white', color='orange')
            self.select_button.on_clicked(self.make_event_selector)

        if self.domain_selection is None:
            domain_ax = plt.axes([0.92, 0.84, 0.06, 0.05])
            self.domain_selection = RadioButtons(domain_ax, ('Time', 'Freq'))
            self.domain_selection.on_clicked(self.switch_domain)

    def make_event_selector(self, event):
        self.stop_play(event)
        self.event_selector = Viewer.EventSelector(parent = self)


    def handle_keys(self, event):
        #print(event.key)
        if event.key is ' ':
            if self.playing is True:
                self.stop_play(event)
            else:
                self.start_play(event)
        elif event.key is 'right':
            self.forward(event)
        elif event.key is 'left':
            self.backward(event)

        elif event.key is 'up':
            self.set_entry(self.entry + 1000)
        elif event.key is 'down':
            self.set_entry(self.entry - 1000)

        elif event.key is 'd':
            if self.domain is Domain.Time:
                self.switch_domain('Freq')
            else:
                self.switch_domain('Time')
        elif event.key is 'j':
            self.make_event_selector(event)


    class EventSelector():
    	def __init__(self, parent = None):
    	    self.parent = parent

    	    self.fig = plt.figure()

    	    self.run_ax = plt.axes([0.3, 0.9, 0.5, 0.1])
    	    self.run_selection = TextBox(self.run_ax, 'Run', initial = str(self.parent.run), color = 'white',  hovercolor = 'lightgrey')
    	    self.run_selection.on_submit(self.submit_run)

    	    self.entry_ax = plt.axes([0.3, 0.8, 0.5, 0.1])
    	    self.entry_selection = TextBox(self.entry_ax, 'Entry', initial = str(self.parent.entry), color = 'white',  hovercolor = 'lightgrey')
    	    self.entry_selection.on_submit(self.submit_entry)

    	    self.event_ax = plt.axes([0.3, 0.7, 0.5, 0.1])
    	    self.event_selection = TextBox(self.event_ax, 'Event', initial = str(self.parent.event_analyzer.header.event_number), color = 'white',  hovercolor = 'lightgrey')
    	    #self.event_selection.on_submit(self.parent.set_event)
    	    self.event_selection.on_submit(self.submit_event)

    	    self.set_values()

    	    plt.ion()
    	    self.fig.show()

    	def submit_event(self, event):
    	    try:
    	        self.parent.set_event(event)
    	        self.set_values()
    	    except:
    	        self.event_selection.color = 'red'
    	        pass

    	def submit_entry(self, entry):
    	    try:
    	        self.parent.set_entry(entry)
    	        self.set_values()
    	    except:
    	        self.entry_selection.color = 'red'

    	def submit_run(self, run):
    	    try:
    	        self.parent.set_run(run)
    	        self.set_values()
    	    except:
    	        self.run_selection.color = 'red'

    	def set_values(self):
    	    self.run_selection.set_val(str(self.parent.run))
    	    self.entry_selection.set_val(str(self.parent.entry))
    	    self.event_selection.set_val(str(self.parent.event_analyzer.header.event_number))

    	    for selection in [self.run_selection, self.entry_selection, self.event_selection]:
    	        selection.color = 'white'

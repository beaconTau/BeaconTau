from .DataDirectory import DataDirectory
from .RunAnalyzer import RunAnalyzer
from matplotlib import pyplot as plt

#from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.widgets import Button

from enum import Enum

class Domain(Enum):
    Time = 0
    Freq = 1

class Viewer():
    """
    A class to manage the viewing of events.
    And that's it.
    """
    
    def __init__(self, run = None, data_dir = None):
        self.dd = DataDirectory(data_dir)
        self.run = run
        if self.run is None:
            self.run = self.dd.runs[0]
        print(self.run)
        self.run_analyzer = self.dd.run(self.run)
        self.entry = 0
        self.event_analyzer = self.run_analyzer.get_entry(self.entry)
        self.n_rows = 2

        self.domain = Domain.Time
        self.log_scale = False

        self.fig = None
        self.axes = None

        self.next_button = None
        self.prev_button = None

        self.play_button = None
        self.stop_button = None
        self.timer = None
        self.playing = False

        plt.ion()
        plt.show()

        self.update()

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
            self.timer = self.fig.canvas.new_timer(10)
            self.timer.add_callback(self.forward, None)
        self.timer.start()

    def stop_play(self, event):
        self.playing = False
        self.timer.stop()
        
    def __repr__(self):
        return '<BeaconTau.Viewer run ' + self.run + ' event ' + self.event_analyzer.header.event_number + '>'

    def update(self):
        # Draw the event in Matplotlib

        for board in self.event_analyzer.event.data:

            # TODO add check on axes length if extenal set of axes passed in
            # TODO for multiple boards, maybe that's overkill...
            if self.axes is None:
                n_cols = int(len(board)/self.n_rows)
                self.fig, self.axes = plt.subplots(self.n_rows, n_cols, sharey = True, sharex = True)
                mng = plt.get_current_fig_manager()
                mng.resize(*mng.window.maxsize())
            for chan in range(len(board)):
                self.axes.flat[chan].set_title('Channel ' + str(chan+1))
                color = 'C' + str(chan) # matplotlib accepts strings beginning with a capital C for colors
                self.axes.flat[chan].clear()
                if self.domain is Domain.Time:
                    self.axes.flat[chan].plot(self.event_analyzer.times(),  self.event_analyzer.channel(chan), color)
                    self.axes.flat[chan].set_xlabel('Time (ns)')
                    self.axes.flat[chan].set_ylabel('Amplitude (mV)')
                else:
                    self.axes.flat[chan].set_xlabel('Freq (MHz)')
                    if self.log_scale is True:
                        self.axes.flat[chan].plot(self.event_analyzer.freqs(), self.event_analyzer.channel_psd_db(chan), color)
                        self.axes.flat[chan].set_ylabel('PSD (dB)')
                    else:
                        self.axes.flat[chan].plot(self.event_analyzer.freqs(), self.event_analyzer.channel_psd(chan), color)
                        self.axes.flat[chan].set_ylabel('PSD (mV^{2} / MHz)')
            plt.suptitle('Event ' + str(self.event_analyzer.event.event_number))

        hover_color = 'white'
        # For these btton axes the list is [left, bottom, width, height]
        if self.play_button is None:
            play_ax = plt.axes([0.8, 0.95, 0.1, 0.05])
            self.play_button = Button(play_ax, 'Play', hovercolor='green', color='lightgreen')
            self.play_button.on_clicked(self.start_play)

        if self.stop_button is None:
            stop_ax = plt.axes([0.9, 0.95, 0.1, 0.05])
            self.stop_button = Button(stop_ax, 'Stop', hovercolor='darkred', color='red')
            self.stop_button.on_clicked(self.stop_play)
        
        if self.next_button is None:
            next_ax = plt.axes([0.8, 0.9, 0.1, 0.05])
            self.next_button = Button(next_ax, 'Next', hovercolor='blue', color='lightblue')
            self.next_button.on_clicked(self.forward)

        if self.prev_button is None:
            prev_ax = plt.axes([0.9, 0.9, 0.1, 0.05])
            self.prev_button = Button(prev_ax, 'Prev', hovercolor='yellow', color='lightyellow')
            self.prev_button.on_clicked(self.backward)

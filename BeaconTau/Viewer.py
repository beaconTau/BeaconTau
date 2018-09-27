from BeaconTau import NUM_BEAMS
from .DataDirectory import DataDirectory
from .RunAnalyzer import RunAnalyzer
from matplotlib import pyplot as plt

#from matplotlib.widgets import Slider, Button, RadioButtons
from matplotlib.widgets import Button, TextBox, RadioButtons

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

        self.run = None
        if run is None:
            run = self.dd.runs[-1] # Get the most recent

        self.n_rows = 2

        self.domain = Domain.Time
        self.log_scale = True #False

        self.fig = None
        self.axes = None

        self.next_button = None
        self.prev_button = None

        self.play_button = None
        self.stop_button = None
        self.timer = None
        self.playing = False

        self.run_selection = None
        self.domain_selection = None
        self.trigger_beam_texts = None

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
            self.timer = self.fig.canvas.new_timer(10)
            self.timer.add_callback(self.forward, None)
        self.timer.start()

    def stop_play(self, event):
        self.playing = False
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

        # Put the run we actually have back in the text box
        if self.run_selection is not None:
            self.run_selection.set_val(str(self.run))

    def __repr__(self):
        return '<BeaconTau.Viewer run ' + self.run + ' event ' + self.event_analyzer.header.event_number + '>'

    def update_header_text(self):
        if self.trigger_beam_texts is None:
            self.trigger_beam_texts = {}
            for beam in range(NUM_BEAMS):
                height = 0.03
                x = 0.93
                y = 0.89 - (beam+1)*height
                self.trigger_beam_texts[beam] = plt.figtext(x, y, 'Beam ' + str(beam).zfill(2), bbox=dict(facecolor='white'))

        for beam in range(NUM_BEAMS):
            if self.event_analyzer.beam_triggered(beam):
                self.trigger_beam_texts[beam].set_backgroundcolor('red')
            else:
                self.trigger_beam_texts[beam].set_backgroundcolor('white')

    def update(self):
        for board in self.event_analyzer.event.data:

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
                    self.axes.flat[chan].set_ylabel('Amplitude (ADC)')
                else:
                    self.axes.flat[chan].set_xlabel('Freq (MHz)')
                    if self.log_scale is True:
                        self.axes.flat[chan].plot(self.event_analyzer.freqs()[1:], self.event_analyzer.channel_psd_db(chan)[1:], color)
                        self.axes.flat[chan].set_ylabel('PSD (dB)')
                    else:
                        self.axes.flat[chan].plot(self.event_analyzer.freqs()[1:], self.event_analyzer.channel_psd(chan)[1:], color)
                        self.axes.flat[chan].set_ylabel('PSD (mV**2 / MHz)')
            plt.suptitle('Run ' + str(self.run) + ' Event ' + str(self.event_analyzer.event.event_number))

            self.update_header_text()

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

        if self.run_selection is None:
            run_ax = plt.axes([0.02, 0.95, 0.05, 0.03])
            self.run_selection = TextBox(run_ax, 'Run', initial = str(self.run), color = 'white',  hovercolor = 'lightgrey')
            self.run_selection.on_submit(self.set_run)

        if self.domain_selection is None:
            domain_ax = plt.axes([0.02, 0.89, 0.05, 0.06])
            self.domain_selection = RadioButtons(domain_ax, ('Time', 'Freq'))
            self.domain_selection.on_clicked(self.switch_domain)

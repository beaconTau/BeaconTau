from _BeaconTau import * # This imports the c++ defined code from BeaconTau.cpp
import matplotlib.pyplot as plt
from scipy import signal
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

    def beam_triggered(self, beam):
        if beam < 0 or beam >= NUM_BEAMS:
            return 0
        else:
            return ((self.header.triggered_beams & (1<<beam)) > 0)

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
        plt.ion()
        plt.show()

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

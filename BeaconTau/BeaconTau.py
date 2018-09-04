from _BeaconTau import *
import matplotlib.pyplot as plt

#class Event(Event):
#    def __init__(self):
#        _BEACON.Event.__init__(self)
#        self._n_plot_rows = 2
#
#    def plot(self):
#        for board in self.data:
#            n_col = int(len(board)/self._n_plot_rows)
#            fig, axes = plt.subplots(self._n_plot_rows, n_col, sharey = True)
#            for channel, waveform in enumerate(board):
#                axes.flat[channel].plot(np.trim_zeros(waveform))
#                axes.flat[channel].set_title('Channel' + str(channel+1))
#        plt.show()

#class status(nuphase_status):
#    def __init__(self):
#        nuphase_status.__init__(self)
#
#class event_reader(raw_event_reader):
#    def __init__(self, run, data_dir):
#        raw_event_reader.__init__(self, run, data_dir)
#

if __name__ == '__main__':
    r = RunReader(99, '../../data')

    #e = Event(r.events[0])
    #e.plot()

    evs = [h.event_number for h in r.headers]
    rot = [st.readout_time for st in r.statuses]
    threshs = [st.trigger_thresholds for st in r.statuses]
    threshs2 = list(map(list, zip(*threshs)))
    plt.xlabel('Time (seconds)')
    plt.ylabel('Threshold (???)')
    plt.title('BEACON Thresholds')
    for channel, t in enumerate(threshs2, 1):
        plt.plot(rot, t, label = 'Channel' + str(channel))
    plt.legend()

    plt.show()


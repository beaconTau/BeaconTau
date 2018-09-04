import BeaconTau
from bokeh.plotting import figure, gridplot, curdoc
from bokeh.models import ColumnDataSource

import bokeh.palettes as bpal
from bokeh.layouts import row, column
from bokeh.models.widgets import Button, Toggle, Div

import numpy as np

from bokeh.server.server import Server
from bokeh.application import Application
from bokeh.application.handlers.function import FunctionHandler

from datetime import datetime
from time import sleep

from scipy import signal
from math import log10

class Flame:
    """(Facility for Live Action Monitoring of Events) The online event viewer for BeaconTau"""
    def __init__(self):
        self.run = 99
        self.event_lines = {}
        self.event_plots = {}

        self.current_entry = 0
        self.play_state = 0
        self.rev_state = 0

        self.dt = 2.0 #e-9 #ns 500 Mega Samples Per Second

        self.reader = BeaconTau.RunReader(self.run, '../../../data')
        self.title_div = Div(text = "BEACON FLAME (Facility for Live Action Monitoring of Events)")
        self.header_div = Div(text = self.get_header_text())
        self.b_play = None
        self.b_rev = None
        self.freq_domain = False

        self.setup_graphics()

    def get_header_text(self):
        h = self.reader.headers[self.current_entry]
        time_text = datetime.fromtimestamp(h.readout_time[0]).strftime('%Y-%m-%d %H:%M:%S')
        text = "Run "  + str(self.run) + " event " + str(h.event_number) + " (" + time_text + ")"
        return text


    def create_event_plot(self):
        e = self.reader.events[self.current_entry]
        h = self.reader.headers[self.current_entry]
        board_plots = []

        for board, board_channels in enumerate(e.data):
            plots = []
            if board not in self.event_lines:
                self.event_lines[board] = {}
                self.event_plots[board] = {}

            for channel, waveform in enumerate(board_channels):
                chan_title = 'Channel ' + str(channel+1)
                p = figure(title = chan_title, plot_width = 400, plot_height = 200, output_backend="webgl", tools="", toolbar_location = None, logo = None)
                source = ColumnDataSource({'x' : [], str(channel) : []})
                self.event_plots[board][channel] = p
                self.event_lines[board][channel] = p.line(x = 'x', y = str(channel), source = source, color = bpal.Category20[len(board_channels)*2][channel*2])

                if channel > 0:
                    p.y_range = plots[0].y_range
                plots.append(p)


            half_n = int(len(plots)/2)
            top_row = plots[:half_n]
            bottom_row = plots[half_n:]
            p = gridplot(top_row, bottom_row)
            board_plots.append(p)

        self.update_events(self.current_entry)
        return column(board_plots)

    def toggle_domain(self, state):
        self.freq_domain = state
        self.update_events(self.current_entry)

    def toggle_play(self, state):
        self.play_state = state
        if self.play_state > 0:
            self.b_play.label = 'Pause'
            self.play_callback_id = curdoc().add_periodic_callback(self.next_event, 1000)
        else:
            self.b_play.label = 'Play'
            curdoc().remove_periodic_callback(self.play_callback_id)

    def toggle_reverse(self, state):
        self.rev_state = state
        if self.rev_state > 0:
            self.b_rev.label = 'Pause'
            self.rev_callback_id = curdoc().add_periodic_callback(self.previous_event, 1000)
        else:
            self.b_rev.label = 'Reverse'
            curdoc().remove_periodic_callback(self.rev_callback_id)


    def next_event(self):
        entry = self.current_entry + 1
        self.update_events(entry)


    def previous_event(self):
        entry = self.current_entry - 1
        self.update_events(entry)


    def update_events(self, entry):
        if entry < 0:
            entry = entry + len(self.reader.events)
        elif entry >= len(self.reader.events):
            entry = entry - len(self.reader.events)

        self.current_entry = entry

        e = self.reader.events[self.current_entry]
        self.event_number = self.reader.headers[self.current_entry].event_number
        self.header_div.text = self.get_header_text()

        for board, board_channels in enumerate(e.data):
            channel_data = {}
            for channel, waveform in enumerate(board_channels):
                w = waveform[:e.buffer_length]
                if self.freq_domain == False:
                    if 'x' not in channel_data:
                        t = [self.dt*i for i in range(len(w))]
                        channel_data['x'] = t
                    channel_data[str(channel)] = w
                else:
                    df = 1e3/(len(w)*self.dt) # 1e3 GHz -> MHz
                    freqs, Pxx_den = signal.periodogram(w, df)
                    Pxx_den = [10*log10(y) if y > 0 else -40 for y in Pxx_den]
                    if 'x' not in channel_data:
                        channel_data['x'] = freqs[1:]
                    channel_data[str(channel)] = Pxx_den[1:]


            curdoc().hold()
            for channel in range(len(board_channels)):
                if channel in self.event_lines[board]:
                    self.event_lines[board][channel].data_source.data = channel_data

                    if self.freq_domain:
                        self.event_plots[board][channel].xaxis.axis_label = 'Frequency (MHz)'
                        self.event_plots[board][channel].yaxis.axis_label = 'PSD (???)'
                    else:
                        self.event_plots[board][channel].xaxis.axis_label = 'Time (ns)'
                        self.event_plots[board][channel].yaxis.axis_label = 'Amplitude (mV)'
            curdoc().unhold()

    def plot_thresholds(self):
        p = figure(title = 'Thresholds', plot_width=1600, plot_height=400, toolbar_location = None,  tools = "", logo = None)
        long_cols = bpal.Category20[20] + bpal.Category20b[20] + bpal.Category20c[20]
        rot = [st.readout_time for st in self.reader.statuses]
        threshs = [st.trigger_thresholds for st in self.reader.statuses]
        threshs2 = list(map(list, zip(*threshs)))
        for i, thresh in enumerate(threshs2):
            leg_text = 'Beam ' + str(i+1)
            p.line(rot,thresh,color=long_cols[i], legend = leg_text, line_width=2)

        p.legend.click_policy="hide"

        return p

    def setup_graphics(self):

        p1 = self.create_event_plot()
        p2 = self.plot_thresholds()

        b_next = Button(label="Next", button_type="success", width = 400)
        b_next.on_click(self.next_event)

        b_prev = Button(label="Prev", button_type="success", width = 400)
        b_prev.on_click(self.previous_event)

        self.b_play = Toggle(label = "Play", button_type = "success",  width = 400)
        self.b_play.on_click(self.toggle_play)

        self.b_rev = Toggle(label = "Rev", button_type = "success",  width = 400)
        self.b_rev.on_click(self.toggle_reverse)

        self.b_domain = Toggle(label = 'Freq', button_type="success", width = 400)
        self.b_domain.on_click(self.toggle_domain)
        #self.b_average = Toggle(label = 'Average', button_type="success", width = 400)

        b1 = row([self.b_play, self.b_rev])
        b2 = row([b_prev, b_next])
        b3 = row([self.b_domain])

        curdoc().title = 'BEACON FLAME'
        curdoc().add_root(self.title_div)
        curdoc().add_root(self.header_div)
        curdoc().add_root(b1)
        curdoc().add_root(b2)
        curdoc().add_root(b3)
        curdoc().add_root(p1)
        curdoc().add_root(p2)

if __name__ == '__main__':
    pass
elif 'bk_script' in __name__:
    # Then this was called by bokeh serve
    # So we create an instance of the web viewer
    f = Flame()

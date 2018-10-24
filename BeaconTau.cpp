#ifndef BEACON_PYTHON_BINDINGS_H
#define BEACON_PYTHON_BINDINGS_H

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>

#include "beacon.h"
#include "FileReader.h"

namespace py = pybind11;




PYBIND11_MODULE(_BeaconTau, m) {
  m.doc() = "Python module for the BEACON experiment";
  m.def("struct_sizes", &_BeaconTau::struct_sizes, "Get a string showing the struct sizes");
  m.attr("NUM_CHAN")            = BN_NUM_CHAN;
  m.attr("NUM_BUFFER")          = BN_NUM_BUFFER;
  m.attr("MAX_WAVEFORM_LENGTH") = BN_MAX_WAVEFORM_LENGTH;
  m.attr("MAX_BOARDS")          = BN_MAX_BOARDS;
  m.attr("NUM_BEAMS")           = BN_NUM_BEAMS;
  m.attr("NUM_SCALERS")         = BN_NUM_SCALERS;

  py::enum_<beacon_trigger_type>(m,"TrigType")
    .value("NP_TRIG_NONE", beacon_trigger_type::BN_TRIG_NONE)
    .value("NP_TRIG_SW",   beacon_trigger_type::BN_TRIG_SW)
    .value("NP_TRIG_RF",   beacon_trigger_type::BN_TRIG_RF)
    .value("NP_TRIG_EXT",  beacon_trigger_type::BN_TRIG_EXT)
    .export_values();


  py::enum_<beacon_trigger_polarization>(m,"Pol")
    .value("H", beacon_trigger_polarization::H)
    .value("V", beacon_trigger_polarization::V)
    .export_values();

  py::class_<beacon_header>(m, "Header")
    .def(py::init<>())
    .def_readonly("event_number",              &beacon_header::event_number)
    .def_readonly("trig_number",               &beacon_header::trig_number)
    .def_readonly("buffer_length",             &beacon_header::buffer_length)
    .def_readonly("pretrigger_samples",        &beacon_header::pretrigger_samples)
    .def_readonly("readout_time",              &beacon_header::readout_time)
    .def_readonly("approx_trigger_time",       &beacon_header::approx_trigger_time)
    .def_readonly("approx_trigger_time_nsecs", &beacon_header::approx_trigger_time_nsecs)
    .def_readonly("triggered_beams",           &beacon_header::triggered_beams)
    .def_readonly("beam_mask",                 &beacon_header::beam_mask)
    .def_readonly("beam_power",                &beacon_header::beam_power)
    .def_readonly("deadtime",                  &beacon_header::deadtime)
    .def_readonly("buffer_number",             &beacon_header::buffer_number)
    .def_readonly("channel_mask",              &beacon_header::channel_mask)
    .def_readonly("channel_read_mask",         &beacon_header::channel_read_mask)
    .def_readonly("gate_flag",                 &beacon_header::gate_flag)
    .def_readonly("buffer_mask",               &beacon_header::buffer_mask)
    .def_readonly("board_id",                  &beacon_header::board_id)
    .def_readonly("trig_type",                 &beacon_header::trig_type)
    .def_readonly("trig_pol",                  &beacon_header::trig_pol)
    .def_readonly("calpulser",                 &beacon_header::calpulser)
    .def_readonly("sync_problem",              &beacon_header::sync_problem)
    .def("__repr__", [](const beacon_header &h) {
		       static std::string s;
		       s = "<BeaconTau.Header " + std::to_string(h.event_number) + ">";
		       return s;
		     });



  py::class_<beacon_event>(m, "Event")
    .def(py::init<>())
    // .def("read", &_BeaconTau::event::read)
    .def_readonly("event_number",    &beacon_event::event_number)
    .def_readonly("buffer_length",   &beacon_event::buffer_length)
    .def_readonly("board_id",        &beacon_event::board_id)
    .def_readonly("data",            &beacon_event::data)
    .def("__repr__", [](const beacon_event& e) {
    		       static std::string s;
    		       s = "<BeaconTau.Event " + std::to_string(e.event_number) + ">";
    		       return s;
    		     })
    ;


  py::class_<beacon_status>(m, "Status")
    .def(py::init<>())
    .def_readonly("global_scalers",     &beacon_status::global_scalers)
    .def_readonly("beam_scalers",       &beacon_status::beam_scalers)
    .def_readonly("deadtime",           &beacon_status::deadtime)
    .def_readonly("readout_time",       &beacon_status::readout_time)
    .def_readonly("readout_time_ns",    &beacon_status::readout_time_ns)
    .def_readonly("trigger_thresholds", &beacon_status::trigger_thresholds)
    .def_readonly("latched_pps_time",   &beacon_status::latched_pps_time)
    .def_readonly("board_id",           &beacon_status::board_id)
    .def_readonly("dynamic_beam_mask",  &beacon_status::dynamic_beam_mask)
    .def("__repr__", [](const beacon_status& st){
		       static std::string s;
		       s = "<Status at " + std::to_string(st.readout_time) + "."  + std::to_string(st.readout_time_ns) + ">";
		       return s;
		     });

  py::class_<_BeaconTau::FileReader>(m, "FileReader")
    .def(py::init<int, const std::string&>())
    .def("__repr__",  [](const _BeaconTau::FileReader& r){
			static std::string s;
			s = "<BeaconTau.FileReader for run " + std::to_string(r.run) + ">";
			return s;
		      }) 
    .def_readonly("events", &_BeaconTau::FileReader::events)
    .def_readonly("headers", &_BeaconTau::FileReader::headers)
    .def_readonly("statuses", &_BeaconTau::FileReader::statuses);

#define BEACON_FILE_READER_VECTOR(type, name)				\
  py::class_<_BeaconTau::FileReader::Vector<type> >(m, name)            \
    .def(py::init<const std::string&, size_t>())			\
    .def("__getitem__", &_BeaconTau::FileReader::Vector<type>::at)      \
    .def("__len__",     &_BeaconTau::FileReader::Vector<type>::size)    \
    .def_readwrite("max_files_in_memory", &_BeaconTau::FileReader::Vector<type>::max_files_in_memory) \
    ;

  BEACON_FILE_READER_VECTOR(beacon_header, "FileReader::Headers")
  BEACON_FILE_READER_VECTOR(beacon_status, "FileReader::Statuses")
  BEACON_FILE_READER_VECTOR(beacon_event,  "FileReader::Events")
  
}

#endif //BEACON_PYTHON_BINDINGS_H

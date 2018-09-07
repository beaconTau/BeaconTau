#ifndef BEACON_PYTHON_BINDINGS_H
#define BEACON_PYTHON_BINDINGS_H

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "beacon.h"
#include <dirent.h>
#include <errno.h>

namespace py = pybind11;


/**
 * @namespace _BeaconTau
 * @brief The c++ part of the BeaconTau python module, uses bybind11 to get this into your python interpreter.
 */

namespace _BeaconTau {

  class FileReader {
  public:
    FileReader(int run, const std::string& base_dir)
      : run(run), base_dir(base_dir)
    {
      run_dir = base_dir + "/run" + std::to_string(run) + "/";

      for(auto event_file_name : list_files(run_dir + "event")){
	read_file(event_file_name, events);
      }
      for(auto header_file_name : list_files(run_dir + "header")){
	read_file(header_file_name, headers);
      }
      for(auto status_file_name : list_files(run_dir + "status")){
	read_file(status_file_name, statuses);
      }
    }
    int run; ///< Which run
    std::string base_dir; ///< The data directory containing all the runs
    std::string run_dir; ///< The directory of the run
    std::vector<beacon_event> events;
    std::vector<beacon_header> headers;
    std::vector<beacon_status> statuses;

    std::vector<std::string> list_files (const std::string& dir)
    {
      std::vector<std::string> files;
      DIR *dp = nullptr;
      struct dirent *dirp = nullptr;
      if((dp  = opendir(dir.c_str())) == nullptr) {
	std::cerr << "Error(" << errno << ") opening " << dir << std::endl;
        return files;
      }

      while ((dirp = readdir(dp)) != nullptr) {
        files.emplace_back(dir + "/" + std::string(dirp->d_name));
	if(files.back()=="." || files.back()==".."){
	  files.pop_back();
	}
      }
      std::sort(files.begin(), files.end());
      closedir(dp);
      return files;
    }

    int beacon_generic_read(gzFile gz_file, FILE* file, beacon_status* status){
      if(gz_file != Z_NULL){
	return beacon_status_gzread(gz_file, status);
      }
      else {
	return beacon_status_read(file, status);
      }
    }

    int beacon_generic_read(gzFile gz_file, FILE* file, beacon_header* header){
      if(gz_file != Z_NULL){
	return beacon_header_gzread(gz_file, header);
      }
      else {
	return beacon_header_read(file, header);
      }
    }

    int beacon_generic_read(gzFile gz_file, FILE* file, beacon_event* event){
      if(gz_file != Z_NULL){
	return beacon_event_gzread(gz_file, event);
      }
      else {
	return beacon_event_read(file, event);
      }
    }

    template<class T>
    int read_file(const std::string& file_name, std::vector<T>& ts){

      // If the last four characters are ".tmp" then let's skip these for now
      if(file_name.rfind(".tmp") == file_name.length() - 4){
	return 0;
      }

      gzFile gz_file = Z_NULL;
      FILE* file = nullptr;

      // if the last three characters in the file_name are ".gz"
      if(file_name.rfind(".gz") == file_name.length() - 3){
	// std::cout << file_name << " matches gzip name convention!" << std::endl;
	gz_file = gzopen (file_name.c_str(), "r");
	if(gz_file == Z_NULL){
	  return 0;
	}
      }
      else{
	// std::cout << file_name << " does NOT match gzip name convention!" << std::endl;
	file = fopen(file_name.c_str(),  "r");
	if(file == nullptr){
	  return 0;
	}
      }

      int numEvents = 0;
      int retVal = 0;
      while(retVal == 0){
	ts.emplace_back(T());
	retVal = beacon_generic_read(gz_file, file, &ts.back());
	if(retVal==0){
	  numEvents++;
	}
	else{
	  ts.pop_back();
	}
      }

      if(gz_file != Z_NULL){
	gzclose(gz_file);
      }
      if(file != NULL){
	fclose(file);
      }

      return numEvents;
    }
  };

}




PYBIND11_MODULE(_BeaconTau, m) {
  m.doc() = "Python module for the BEACON experiment";

  // py::enum_<np_io_error_t>(m,"np_io_error_t")
  //   .value("NP_ERR_CHECKSUM_FAILED", np_io_error_t::NP_ERR_CHECKSUM_FAILED)
  //   .value("NP_ERR_NOT_ENOUGH_BYTES", np_io_error_t::NP_ERR_NOT_ENOUGH_BYTES)
  //   .value("NP_ERR_NOT_WRONG", np_io_error_t::NP_ERR_NOT_WRONG)
  //   .value("NP_ERR_BAD_VERSION", np_io_error_t::NP_ERR_BAD_VERSION)
  //   .export_values();


  // /**  Trigger types */
  // typedef enum beacon_trigger_type
  // {
  //  NP_TRIG_NONE,   //<! Triggered by nothing (should never happen but if it does it's a bad sign1)
  //  NP_TRIG_SW,    //!< triggered by software (force trigger)
  //  NP_TRIG_RF,    //!< triggered by input waveforms
  //  NP_TRIG_EXT    //!< triggered by external trigger
  // } beacon_trig_type_t;

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

  // typedef enum beacon_trigger_polarization
  // {
  //  H = 0,
  //  V = 1
  // } beacon_trigger_polarization_t;

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

}

#endif //BEACON_PYTHON_BINDINGS_H

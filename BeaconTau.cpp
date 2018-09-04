#ifndef BEACON_PYTHON_BINDINGS_H
#define BEACON_PYTHON_BINDINGS_H

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "nuphase.h"
#include <dirent.h>
#include <errno.h>

namespace py = pybind11;

namespace BeaconTau {

  class RunReader {
  public:
    RunReader(int run, const std::string& base_dir)
      : run(run), base_dir(base_dir)
    {
      run_dir = base_dir + "/run" + std::to_string(run) + "/";

      for(auto event_file_name : list_files(run_dir + "event")){
	read_event_file(event_file_name);
      }
      for(auto header_file_name : list_files(run_dir + "header")){
	read_header_file(header_file_name);
      }
      for(auto status_file_name : list_files(run_dir + "status")){
	read_status_file(status_file_name);
      }
    }
    int run;
    std::string base_dir;
    std::string run_dir;
    std::vector<nuphase_event> events;
    std::vector<nuphase_header> headers;
    std::vector<nuphase_status> statuses;


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

    
    int read_event_file(const std::string& file_name){

      int numEvents = 0;
      int retVal = 0;

      gzFile file;
      file = gzopen (file_name.c_str(), "r");
      if(file == 0){
	return 0;
      }
      while(retVal == 0){
	events.emplace_back(nuphase_event());
	retVal = nuphase_event_gzread(file, &events.back());
	if(retVal==0){
	  numEvents++;	
	}
	else{
	  events.pop_back();
	}
      }
      return numEvents;
    }


    int read_header_file(const std::string& file_name){

      int numEvents = 0;
      int retVal = 0;

      gzFile file;
      file = gzopen (file_name.c_str(), "r");
      if(file == 0){
	return 0;
      }      
      while(retVal == 0){
	headers.emplace_back(nuphase_header());
	retVal = nuphase_header_gzread(file, &headers.back());
	if(retVal==0){
	  numEvents++;	
	}
	else{
	  headers.pop_back();
	}
      }
      return numEvents;
    }
    
    
    int read_status_file(const std::string& file_name){
      int numEvents = 0;
      int retVal = 0;

      gzFile file;
      file = gzopen (file_name.c_str(), "r");
      if(file == 0){
	return 0;
      }
      while(retVal == 0){
	statuses.emplace_back(nuphase_status());
	retVal = nuphase_status_gzread(file, &statuses.back());
	if(retVal==0){
	  numEvents++;	
	}
	else{
	  statuses.pop_back();
	}
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
  // typedef enum nuphase_trigger_type 
  // {
  //  NP_TRIG_NONE,   //<! Triggered by nothing (should never happen but if it does it's a bad sign1) 
  //  NP_TRIG_SW,    //!< triggered by software (force trigger)  
  //  NP_TRIG_RF,    //!< triggered by input waveforms
  //  NP_TRIG_EXT    //!< triggered by external trigger 
  // } nuphase_trig_type_t;

  py::enum_<nuphase_trigger_type>(m,"TrigType")
    .value("NP_TRIG_NONE", nuphase_trigger_type::NP_TRIG_NONE)
    .value("NP_TRIG_SW",   nuphase_trigger_type::NP_TRIG_SW)
    .value("NP_TRIG_RF",   nuphase_trigger_type::NP_TRIG_RF)
    .value("NP_TRIG_EXT",  nuphase_trigger_type::NP_TRIG_EXT)
    .export_values();  


  py::enum_<nuphase_trigger_polarization>(m,"Pol")
    .value("H", nuphase_trigger_polarization::H)
    .value("V", nuphase_trigger_polarization::V)
    .export_values();  
  
  // typedef enum nuphase_trigger_polarization
  // {
  //  H = 0,
  //  V = 1
  // } nuphase_trigger_polarization_t;
  
  py::class_<nuphase_header>(m, "Header")
    .def(py::init<>())
    .def_readonly("event_number",              &nuphase_header::event_number)
    .def_readonly("trig_number",               &nuphase_header::trig_number)
    .def_readonly("buffer_length",             &nuphase_header::buffer_length)
    .def_readonly("pretrigger_samples",        &nuphase_header::pretrigger_samples)
    .def_readonly("readout_time",              &nuphase_header::readout_time)
    .def_readonly("approx_trigger_time",       &nuphase_header::approx_trigger_time)
    .def_readonly("approx_trigger_time_nsecs", &nuphase_header::approx_trigger_time_nsecs)
    .def_readonly("triggered_beams",           &nuphase_header::triggered_beams)
    .def_readonly("beam_mask",                 &nuphase_header::beam_mask)
    .def_readonly("beam_power",                &nuphase_header::beam_power)
    .def_readonly("deadtime",                  &nuphase_header::deadtime)
    .def_readonly("buffer_number",             &nuphase_header::buffer_number)
    .def_readonly("channel_mask",              &nuphase_header::channel_mask)
    .def_readonly("channel_read_mask",         &nuphase_header::channel_read_mask)
    .def_readonly("gate_flag",                 &nuphase_header::gate_flag)
    .def_readonly("buffer_mask",               &nuphase_header::buffer_mask)
    .def_readonly("board_id",                  &nuphase_header::board_id)
    .def_readonly("trig_type",                 &nuphase_header::trig_type)
    .def_readonly("trig_pol",                  &nuphase_header::trig_pol)
    .def_readonly("calpulser",                 &nuphase_header::calpulser)
    .def_readonly("sync_problem",              &nuphase_header::sync_problem)
    .def("__repr__", [](const nuphase_header &h) {
		       static std::string s;
		       s = "<BeaconTau.Header " + std::to_string(h.event_number) + ">";
		       return s;
		     });



  py::class_<nuphase_event>(m, "Event")
    .def(py::init<>())
    // .def("read", &BeaconTau::event::read)
    .def_readonly("event_number",    &nuphase_event::event_number)
    .def_readonly("buffer_length",   &nuphase_event::buffer_length)
    .def_readonly("board_id",        &nuphase_event::board_id)
    .def_readonly("data",            &nuphase_event::data)
    .def("__repr__", [](const nuphase_event& e) {
    		       static std::string s;
    		       s = "<BeaconTau.Event " + std::to_string(e.event_number) + ">";
    		       return s;
    		     })
    ;
  

  py::class_<nuphase_status>(m, "Status")
    .def(py::init<>())
    .def_readonly("global_scalars",     &nuphase_status::global_scalers)
    .def_readonly("beam_scalers",       &nuphase_status::beam_scalers)
    .def_readonly("deadtime",           &nuphase_status::deadtime)
    .def_readonly("readout_time",       &nuphase_status::readout_time)
    .def_readonly("readout_time_ns",    &nuphase_status::readout_time_ns)
    .def_readonly("trigger_thresholds", &nuphase_status::trigger_thresholds)
    .def_readonly("latched_pps_time",   &nuphase_status::latched_pps_time)
    .def_readonly("board_id",           &nuphase_status::board_id)
    .def_readonly("dynamic_beam_mask",  &nuphase_status::dynamic_beam_mask)
    .def("__repr__", [](const nuphase_status& st){
		       static std::string s;
		       
		       s = "<Status at " + std::to_string(st.readout_time) + "."  + std::to_string(st.readout_time_ns) + ">";
		       return s;
		     });

  py::class_<BeaconTau::RunReader>(m, "RunReader")
    .def(py::init<int, const std::string&>())
    .def("__repr__",  [](const BeaconTau::RunReader& r){
			static std::string s;
			s = "<BeaconTau.RunReader for run " + std::to_string(r.run) + ">";
			return s;
		      })
    .def_readonly("events", &BeaconTau::RunReader::events)
    .def_readonly("headers", &BeaconTau::RunReader::headers)
    .def_readonly("statuses", &BeaconTau::RunReader::statuses);  
  
}

#endif //BEACON_PYTHON_BINDINGS_H











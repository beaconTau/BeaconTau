#ifndef BEACON_PYTHON_BINDINGS_H
#define BEACON_PYTHON_BINDINGS_H

#include <pybind11/pybind11.h>
#include <pybind11/numpy.h>
#include <pybind11/stl.h>
#include "beacon.h"
#include <dirent.h>
#include <errno.h>
#include <deque>

namespace py = pybind11;


/**
 * @namespace _BeaconTau
 * @brief The c++ part of the BeaconTau python module
 *
 * C++ code defined here will use pybind11 to get to your python interpreter.
 * This is probably where any low level file manipulation will be implemented.
 */
namespace _BeaconTau {

  /** 
   * Return a string that tells you how big the various structs are
   */
  std::string struct_sizes(){
    static std::string size_string =  ("<event = " + std::to_string(sizeof(beacon_event)) + ">\n"
				       "<header = " + std::to_string(sizeof(beacon_header)) + ">\n"
				       "<status = " + std::to_string(sizeof(beacon_status)) + ">");
    return size_string;
  }

  static std::vector<std::string> list_files (const std::string& dir)
  {
    std::vector<std::string> files;
    DIR *dp = nullptr;
    struct dirent *dirp = nullptr;
    if((dp  = opendir(dir.c_str())) == nullptr) {
      std::cerr << "Error(" << errno << ") opening " << dir << std::endl;
      return files;
    }

    while ((dirp = readdir(dp)) != nullptr) {
      std::string name(dirp->d_name);
      if(name!="." && name!=".."){
	files.emplace_back(dir + "/" + name);
      }      
    }
    std::sort(files.begin(), files.end());
    closedir(dp);
    return files;
  }

  int generic_read(gzFile gz_file, FILE* file, beacon_status* status){
    if(gz_file != Z_NULL){
      return beacon_status_gzread(gz_file, status);
    }
    else {
      return beacon_status_read(file, status);
    }
  }

  int generic_read(gzFile gz_file, FILE* file, beacon_header* header){
    if(gz_file != Z_NULL){
      return beacon_header_gzread(gz_file, header);
    }
    else {
      return beacon_header_read(file, header);
    }
  }

  int generic_read(gzFile gz_file, FILE* file, beacon_event* event){
    if(gz_file != Z_NULL){
      return beacon_event_gzread(gz_file, event);
    }
    else {
      return beacon_event_read(file, event);
    }
  }

  template<class T>
  static int read_file(const std::string& file_name, std::vector<T>& ts, size_t max_elements = 0){

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
      retVal = generic_read(gz_file, file, &ts.back());
      if(retVal==0){
	numEvents++;
      }
      else{
	ts.pop_back();
      }
      // don't read more than max_elements
      if(max_elements > 0 && ts.size() >= max_elements){
	break;
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
  
  /**
   * @class FileReader
   * @brief Open the binary data and put it in memory, gzipped or otherwise
   */
  class FileReader {
  public:
    /**
     * @class Vector
     * @brief A container for easy access in python that dynamically reads Beacon data files
     * 
     */
    template<class Content> class Vector {
    private:

      bool maybe_load_file(std::size_t file_index) const {
	std::cout << __PRETTY_FUNCTION__ << "\t" <<  file_index << std::endl;	
	auto it = std::find(read_order.begin(), read_order.end(), file_index);
	for(auto v : read_order){
	  std::cout << v << std::endl;
	}
	if(it != read_order.end()){
	  // then we are already in memory, so do nothing
	  std::cout << "already  loaded? " << *it << std::endl;
	  return false;
	}
	else {
	  maybe_pop_some_contents();
	  std::vector<Content>& vec = contents[file_index];
	  auto& md = meta_data.at(file_index);
	  read_file(md.name, vec); // then get the contents of the first file
	  if(file_index > 0){
	    md.first_index = meta_data.at(file_index - 1).last_index + 1;
	  }
	  md.last_index = md.first_index + vec.size();
	  read_order.push_front(file_index);
	  std::cout << "size = " << contents[file_index].size() << std::endl;
	  return true;
	}
      }

      int maybe_pop_some_contents() const {
	std::cout << __PRETTY_FUNCTION__ << std::endl;	
	int n_popped = 0;
	if(max_files_in_memory > 0){
	  while(read_order.size() >= max_files_in_memory){
	    // delete that file's contents
	    std::size_t erase_me = read_order.back();
	    contents.erase(erase_me);
	    read_order.pop_back();	    
	    n_popped++;
	  }
	}
	return n_popped;
      }

      std::size_t which_file(size_t content_index) const {
	std::cout << __PRETTY_FUNCTION__ << "\t" << content_index << std::endl;
	//  check the last_file_index
	auto md0 = get_meta_data(last_file_index);
	if(md0 && content_index >= md0->first_index && content_index <= md0->last_index){
	  std::cout << "cache match! " << content_index  << std::endl;
	  maybe_load_file(last_file_index); // double check it's loaded... which I don't think is guarenteed
	  return last_file_index;
	}

	// the only way to do this and be assured of the right answer
	// is to have read in _ALL_ the files preceeding the index we want
	for(std::size_t file_index = 0; file_index < meta_data.size(); file_index++){
	  auto md = get_meta_data(file_index);
	  if(content_index >= md->first_index && content_index <= md->last_index){
	    std::cout << "Trying " << file_index << std::endl;
	    maybe_load_file(file_index); // double check it's loaded... which I don't think is guarenteed
	    last_file_index = file_index;
	    return file_index;
	  }
	}
	std::string error_message = std::to_string(content_index) + " is out of range!";
	throw std::out_of_range(error_message);
	return meta_data.size() + 1;
      }

      class FileMetaData {
      public:
	FileMetaData(const std::string& name) : name(name), first_index(0), last_index(0) {;}
	const std::string name;
	std::size_t first_index;
	std::size_t last_index;
      };

      const FileMetaData* get_meta_data(std::size_t file_index) const {
	std::cout << __PRETTY_FUNCTION__ << "\t"  << file_index << std::endl;
	if(file_index >= meta_data.size()){
	  return nullptr;
	}
	auto& md = meta_data.at(file_index);
	if(md.last_index==0){
	  // we need to populate the first_index and last_index
	  // and the only way to do this is by reading the file itself
	  maybe_load_file(file_index);
	}
	return &meta_data[file_index];
      }
      
      const std::string dir_name; ///< String containing the name of the directory with the BEACON files
      size_t max_files_in_memory = 0; ///< The maximum number files to allow in memory, zero means unlimited
      mutable std::vector<FileMetaData> meta_data; ///< The file names and indices of the first and last entries
      mutable std::map<size_t, std::vector<Content> > contents; ///< Maps index in meta_data to contents of the files in the directory
      mutable std::deque<size_t> read_order; ///< Tracks the order in which files are read in memory
      mutable size_t last_file_index = -1;
      

    public:

      // /**
      //  * @class const_iterator
      //  * @brief Definitely not STL compliant const_iterator for our _BeaconTau::Vector
      //  */
      // class const_iterator {
      // private:
      // 	std::size_t content_index;
      // 	std::size_t file_index;
      // 	const Vector* v;
      // public:
      // 	const_iterator(const Vector* V = nullptr, std::size_t file_index) :
      // 	  v(V), file_index(file_index) {}

      // 	const_iterator& operator++(){
	  
      // 	  size_t file_index = which_file(content_index);
      // 	  return *this;
      // 	}

      // 	const_iterator& operator--(){
      // 	  --index;
      // 	  return *this;
      // 	}

      // 	const Content& operator*(){
      // 	  return v->at(index);
      // 	}

      // 	const Content* operator->(){
      // 	  return &v->at(index);
      // 	}
      // };
      
      
      Vector(const std::string& directory_name) : dir_name(directory_name) {
	std::cout << __PRETTY_FUNCTION__ << std::endl;	
	std::vector<std::string> names = list_files(dir_name); // first get the file names

	for(auto& n : names){
	  std::cout << n << std::endl;
	}
	if(names.size()==0){
	  std::cerr << "Warning in " << __PRETTY_FUNCTION__ << " no files in "  << dir_name;
	}

	for(const std::string& name : names){
	  meta_data.emplace_back(FileMetaData(name));
	}
      }

      const Content& at(size_t content_index) const {
	std::cout << __PRETTY_FUNCTION__ << std::endl;
	size_t file_index = which_file(content_index);
	std::cout << "at() the file_index = " << file_index << std::endl;
	const auto& md = meta_data[file_index];
	std::cout << md.name << std::endl;
	std::cout << content_index - md.first_index << std::endl;
	return contents[file_index].at(content_index - md.first_index);
      }

      const Content& operator[](size_t content_index) const {
	std::cout << __PRETTY_FUNCTION__ << std::endl;	
	return at(content_index);
      }

      // const_iterator begin() const {return const_iterator(this, 0);}
      // const_iterator end() const {return const_iterator(this, meta_data.size();}
      
    };
    
    FileReader(int run, const std::string& base_dir)
      : run(run), base_dir(base_dir), run_dir(base_dir + "/run" + std::to_string(run) + "/"),  events2(run_dir + "event")
    {
      event_file_names =  _BeaconTau::list_files(run_dir + "event");
      header_file_names = _BeaconTau::list_files(run_dir + "header");
      status_file_names = _BeaconTau::list_files(run_dir + "status");

      for(const auto& header_file_name : header_file_names){
	_BeaconTau::read_file(header_file_name, headers);
      }
      for(const auto& status_file_name : status_file_names){
	_BeaconTau::read_file(status_file_name, statuses);
      }
      for(const auto& event_file_name : event_file_names){
      _BeaconTau::read_file(event_file_name, events);
      }      
    }
    int run; ///< Which run
    std::string base_dir; ///< The data directory containing all the runs
    std::string run_dir; ///< The directory of the run
    std::vector<std::string> event_file_names;
    std::vector<std::string> header_file_names;
    std::vector<std::string> status_file_names;
    std::vector<beacon_header> headers;
    std::vector<beacon_status> statuses;
    std::vector<beacon_event> events;
    Vector<beacon_event> events2;
  };

}




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
    .def_readonly("events2", &_BeaconTau::FileReader::events2)
    .def_readonly("headers", &_BeaconTau::FileReader::headers)
    .def_readonly("statuses", &_BeaconTau::FileReader::statuses);

  py::class_<_BeaconTau::FileReader::Vector<beacon_event> >(m, "FileReader::EventVector")
    .def(py::init<const std::string&>())
    .def("__getitem__",  [](const _BeaconTau::FileReader::Vector<beacon_event> &v, size_t i){
			   std::cout << "hello" << std::endl;
			   auto& e = v.at(i);
			   std::cout << e.event_number << std::endl;
			   return e;
			 });
  
}

#endif //BEACON_PYTHON_BINDINGS_H

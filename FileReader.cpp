#include "FileReader.h"
#include "dirent.h"
#include <algorithm>

std::string _BeaconTau::struct_sizes(){
  static std::string s = ("beacon_header = " + std::to_string(sizeof(beacon_header)) + ", "
			  + "beacon_status = " + std::to_string(sizeof(beacon_status)) + ", "
			  + "beacon_event = "  + std::to_string(sizeof(beacon_event)));
  return s;
}

std::vector<std::string> _BeaconTau::list_files (const std::string& dir, const std::string& regexp){
  std::vector<std::string> ignore_these = {"..", "."};
  std::vector<std::string> file_names;
  struct dirent* dirp = nullptr;
  DIR *dp = opendir(dir.c_str());
  if(dp == nullptr) {
    std::string error_message = "Error(" + std::to_string(errno) + ") opening " + dir;
    throw std::runtime_error(error_message);
  }

  while ((dirp = readdir(dp)) != nullptr) {
    std::string name(dirp->d_name);

    bool file_name_good = true;
    for(const auto& ignore_me : ignore_these){
      if(name == ignore_me){
	file_name_good = false;
	break;
      }
    }

    if(file_name_good){
      file_names.emplace_back(dir + "/" + name);
    }
  }
  std::sort(file_names.begin(), file_names.end());
  closedir(dp);
  return file_names;
}


int _BeaconTau::generic_read(gzFile gz_file, FILE* file, beacon_status* status){
  if(gz_file != Z_NULL){
    return beacon_status_gzread(gz_file, status);
  }
  else {
    return beacon_status_read(file, status);
  }
}

int _BeaconTau::generic_read(gzFile gz_file, FILE* file, beacon_header* header){
  if(gz_file != Z_NULL){
    return beacon_header_gzread(gz_file, header);
  }
  else {
    return beacon_header_read(file, header);
  }
}

int _BeaconTau::generic_read(gzFile gz_file, FILE* file, beacon_event* event){
  if(gz_file != Z_NULL){
    return beacon_event_gzread(gz_file, event);
  }
  else {
    return beacon_event_read(file, event);
  }
}








_BeaconTau::FileReader::FileReader(int run, const std::string& base_dir)
  : run(run), base_dir(base_dir), run_dir(base_dir + "/run" + std::to_string(run) + "/"),
    // somewhat random numbers picked here for the max_files in memory
    // should be about 10 MB per type. Obviously this means more reading per iteration.
    // @todo make this configurable somehow...
    headers(run_dir + "header", 1000),
    statuses(run_dir + "status", 300),
    events(run_dir + "event", 3) 
{ }









// // template<class Content>
// // int _BeaconTau::read_file(const std::string& file_name, std::vector<Content>& contents, size_t max_elements){


// // }


// template <class Content>
// bool _BeaconTau::FileReader::Vector<Content>::maybe_load_file(std::size_t file_index) const {
// }

// template <class Content>
// int _BeaconTau::FileReader::Vector<Content>::maybe_pop_some_contents() const {
// }

// template <class Content>
// std::size_t _BeaconTau::FileReader::Vector<Content>::which_file(size_t content_index) const {
// }

// template <class Content>
// const _BeaconTau::FileReader::FileMetaData* _BeaconTau::FileReader::Vector<Content>::get_meta_data(std::size_t file_index) const {
// }
      

// template <class Content>
// _BeaconTau::FileReader::Vector<Content>::Vector(const std::string& directory_name, size_t max_files_in_RAM)
// }


// template <class Content>
// const Content& _BeaconTau::FileReader::Vector<Content>::at(size_t content_index) const {
// }

// template <class Content>
// std::size_t _BeaconTau::FileReader::Vector<Content>::size() const {
// }      



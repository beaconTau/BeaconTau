#include "FileReader.h"
#include "dirent.h"
#include <algorithm>

template class _BeaconTau::FileReader::Vector<beacon_header>;
template class _BeaconTau::FileReader::Vector<beacon_status>;
template class _BeaconTau::FileReader::Vector<beacon_event>;

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







template<class Content>
int _BeaconTau::read_file(const std::string& file_name, std::vector<Content>& contents, size_t max_elements){
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
      contents.emplace_back(Content());
      retVal = generic_read(gz_file, file, &contents.back());
      if(retVal==0){
	numEvents++;
      }
      else{
	contents.pop_back();
      }
      // don't read more than max_elements
      if(max_elements > 0 && contents.size() >= max_elements){
	break;
      }
    }
    if(gz_file != Z_NULL){
      gzclose(gz_file);
    }
    if(file != NULL){
      fclose(file);
    }
    // std::cout << "read_file" << "\t" << numEvents << "\t" << ts.size() << std::endl;
    return numEvents;
}


template <class Content>
bool _BeaconTau::FileReader::Vector<Content>::maybe_load_file(std::size_t file_index) const {
  auto it = std::find(read_order.begin(), read_order.end(), file_index);
  if(it != read_order.end()){
    // then the file is already in memory, so do nothing
    return false;
  }
  else {
    maybe_pop_some_contents();
    std::vector<Content>& vec = contents[file_index];
    auto& md = meta_data.at(file_index);
    read_file(md.name, vec); // then get the contents of the first file
    if(file_index > 0){
      if(meta_data.at(file_index - 1).last_index == 0){
	maybe_load_file(file_index - 1);
      }
      md.first_index = meta_data.at(file_index - 1).last_index;
    }
    md.last_index = md.first_index + vec.size();
    md.file_index = file_index;
    read_order.push_front(file_index);
    return true;
  }
}
  

template <class Content>
int _BeaconTau::FileReader::Vector<Content>::maybe_pop_some_contents() const {
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


template <class Content>
std::size_t _BeaconTau::FileReader::Vector<Content>::which_file(size_t content_index) const { 
  // check the most frequent case, that the last file is the one we want.
  if(last_meta_data && content_index >= last_meta_data->first_index && content_index < last_meta_data->last_index){
    maybe_load_file(last_meta_data->file_index); // double check it's loaded... which I don't think is guarenteed
    return last_meta_data->file_index;
  }

  // the only way to do this and be assured of the right answer
  // is to have read in _ALL_ the files preceeding the index we want
  for(std::size_t file_index = 0; file_index < meta_data.size(); file_index++){
    auto md = get_meta_data(file_index);
    if(content_index >= md->first_index && content_index < md->last_index){
      maybe_load_file(file_index); // double check it's loaded... which I don't think is guarenteed
      last_meta_data = md;
      return file_index;
    }
  }
  std::string error_message = std::to_string(content_index) + " is out of range!";
  throw std::out_of_range(error_message);
  return meta_data.size() + 1;
}

template <class Content>
const _BeaconTau::FileReader::FileMetaData* _BeaconTau::FileReader::Vector<Content>::get_meta_data(std::size_t file_index) const {
  // std::cout << "get_meta_data" << "\t"  << file_index << std::endl;
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
  

      

template <class Content>
_BeaconTau::FileReader::Vector<Content>::Vector(const std::string& directory_name, size_t max_files_in_RAM)
  : dir_name(directory_name), max_files_in_memory(max_files_in_RAM)
{
  std::vector<std::string> names = list_files(dir_name); // first get the file names
  if(names.size()==0){
    std::stringstream error_message;
    error_message << "Warning in " << __PRETTY_FUNCTION__ << " no files in " << dir_name;
    throw std::out_of_range(error_message.str());
  }

  for(const std::string& name : names){
    meta_data.emplace_back(FileMetaData(name));
  }
}  


template <class Content>
const Content& _BeaconTau::FileReader::Vector<Content>::at(size_t content_index) const {
  size_t file_index = which_file(content_index);
  const auto& md = meta_data[file_index];
  return contents[file_index].at(content_index - md.first_index);
}


template <class Content>
std::size_t _BeaconTau::FileReader::Vector<Content>::size() const {
  return get_meta_data(meta_data.size()-1)->last_index;
}



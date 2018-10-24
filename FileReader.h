#ifndef BEACON_FILE_READER_H
#define BEACON_FILE_READER_H

#include "beacon.h"
#include <string>
#include <vector>
#include <map>
#include <deque>
#include <sstream>
#include <algorithm>

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
  std::string struct_sizes();
  std::vector<std::string> list_files (const std::string& dir, const std::string& regexp = "");
  int generic_read(gzFile gz_file, FILE* file, beacon_status* status);
  int generic_read(gzFile gz_file, FILE* file, beacon_header* header);
  int generic_read(gzFile gz_file, FILE* file, beacon_event* event);

  template<class Content>
  int read_file(const std::string& file_name, std::vector<Content>& contents, size_t max_elements = 0){
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

  

  /**
   * @class FileReader
   * @brief Open the binary data and put it in memory, gzipped or otherwise
   */
  class FileReader {
  public:

    class FileMetaData {
      public:
      FileMetaData(const std::string& name) : name(name), first_index(0), last_index(0) {;}
      const std::string name;
      std::size_t first_index;
      std::size_t last_index;
      std::size_t file_index;
    };

    
    /**
     * @class Vector
     * @brief A container for easy access in python that dynamically reads Beacon data files
     * 
     * Designed to iterate forwards over the data, will be a bit inefficient otherwise.
     */
    template<class Content> class Vector {
    private:
      const std::string dir_name; ///< String containing the name of the directory with the BEACON files
      mutable std::vector<FileMetaData> meta_data; ///< The file names and indices of the first and last entries
      mutable std::map<size_t, std::vector<Content> > contents; ///< Maps index in meta_data to contents of the files in the directory
      mutable std::deque<size_t> read_order; ///< Tracks the order in which files are read in memory
      
      bool maybe_load_file(std::size_t file_index) const{
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
      
      int maybe_pop_some_contents() const{
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

      
      std::size_t which_file(size_t content_index) const{
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

      const FileMetaData* get_meta_data(std::size_t file_index) const{
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

      
      mutable const FileMetaData* last_meta_data = nullptr;

    public:
      std::size_t max_files_in_memory = 0; ///< The maximum number files to allow in memory, zero means unlimited
      Vector(const std::string& directory_name, size_t max_files_in_RAM = 0) : dir_name(directory_name), max_files_in_memory(max_files_in_RAM)
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
      
      const Content& at(size_t content_index) const{
	size_t file_index = which_file(content_index);
	const auto& md = meta_data[file_index];
	return contents[file_index].at(content_index - md.first_index);
      }

      
      std::size_t size() const{
	return get_meta_data(meta_data.size()-1)->last_index;
      }

    };
    
    
      
    FileReader(int run, const std::string& base_dir);
    
    int run; ///< Which run
    std::string base_dir; ///< The data directory containing all the runs
    std::string run_dir; ///< The directory of the run
    Vector<beacon_header> headers; ///< Automagically loaded beacon headers
    Vector<beacon_status> statuses; ///< Automagically loaded beacon statuses
    Vector<beacon_event> events; ///< Automagically loaded beacon events    
  };
  
}



#endif

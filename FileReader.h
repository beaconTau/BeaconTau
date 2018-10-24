#ifndef BEACON_FILE_READER_H
#define BEACON_FILE_READER_H

#include "beacon.h"
#include <string>
#include <vector>
#include <map>
#include <deque>

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
  static std::vector<std::string> list_files (const std::string& dir, const std::string& regexp = "");
  int generic_read(gzFile gz_file, FILE* file, beacon_status* status);
  int generic_read(gzFile gz_file, FILE* file, beacon_header* header);
  int generic_read(gzFile gz_file, FILE* file, beacon_event* event);

  template<class Content>
  int read_file(const std::string& file_name, std::vector<Content>& contents, size_t max_elements = 0);

  

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
      
      bool maybe_load_file(std::size_t file_index) const;
      
      int maybe_pop_some_contents() const;
      std::size_t which_file(size_t content_index) const;

      const FileMetaData* get_meta_data(std::size_t file_index) const;
      mutable const FileMetaData* last_meta_data = nullptr;

    public:
      std::size_t max_files_in_memory = 0; ///< The maximum number files to allow in memory, zero means unlimited
      Vector(const std::string& directory_name, size_t max_files_in_RAM = 0);
      
      const Content& at(size_t content_index) const;
      std::size_t size() const;

    };
    
    
      
    FileReader(int run, const std::string& base_dir);
    
    int run; ///< Which run
    std::string base_dir; ///< The data directory containing all the runs
    std::string run_dir; ///< The directory of the run
    Vector<beacon_header> headers; ///< Automagically loaded beacon headers
    Vector<beacon_status> statuses; ///< Automagically loaded beacon statuses
    Vector<beacon_event> events; ///< Automagically loaded beacon events
    

  private:
    
  };
}


#endif

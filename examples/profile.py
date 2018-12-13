try:
    import ROOT
except:
    raise ImportError('Need pyROOT to compare BeaconTau and beaconroot')

try:
    import gzip

except:
    raise ImportError('Need gzip to fully test BeaconTau I/O speeds')

import random
import shutil
import glob
import os
import time
import BeaconTau as bt

run = 175

def time_me(function):
    def timing_wrapper(*args, **kwargs):
        ts = time.time()
        function_result = function(*args, **kwargs)
        te = time.time()
        timing_wrapper.elapsed = (te - ts)
        if 'print_elasped' in kwargs:
            print('%s took %2f s' % (function.__name__,  timing_wrapper.elapsed))
        return function_result
    return timing_wrapper

@time_me
def init_root():
    beacon_install_dir = os.environ['BEACON_INSTALL_DIR']
    if not beacon_install_dir:
        raise EnvironmentError('Need BEACON_INSTALL_DIR')

    beacon_include_dir = os.environ['BEACON_INSTALL_DIR'] + '/include'
    ROOT.gSystem.AddIncludePath(beacon_install_dir)

    beacon_lib_dir = os.environ['BEACON_INSTALL_DIR'] + '/lib'
    ld_library_path = os.environ['LD_LIBRARY_PATH']
    if beacon_lib_dir not in ld_library_path:
        raise EnvironmentError('Need BEACON_INSTALL_DIR/lib not in LD_LIBRARY_PATH')


@time_me
def read_trees(event_tree, header_tree, num_entries):
    """Assumes you've set the branch address already"""
    #num_entries = header_tree.GetEntries()
    #print('There are %d entries in TTree::%s' % (num_entries, header_tree.GetName()))
    for entry in range(num_entries):
        header_tree.GetEntry(entry)
        event_tree.GetEntry(entry)

@time_me
def random_access_trees(event_tree, header_tree, entry):
    """Assumes you've set the branch address already"""
    header_tree.GetEntry(entry)
    event_tree.GetEntry(entry)

def print_summary(description, times):
    print(description + ': With %d iterations I got mean=%2f s, max=%2f s, min=%2f s' % (len(times), sum(times)/len(times),  max(times), min(times)))


@time_me
def read_beacon_tau_run(run_analyzer, num_entries):
    #num_entries not needed...
    #count = 0
    for event_analyer in run_analyzer.events():
        #count += 1
        pass
    #print('There are %d entries in %s' % (count, repr(run_analyzer)))

@time_me
def random_access_beacon_tau_run(run_analyzer, entry):
    run_analyzer.get_entry(entry)



def gzip_event_files(raw_data_dir):
    files = glob.glob(raw_data_dir + "/*")

    for file_name in files:
        if file_name.endswith('.event'):
            with open(file_name, 'rb') as f_in:
                with gzip.open(file_name + '.gz', 'wb') as f_out:
                    try:
                        shutil.copyfileobj(f_in, f_out)
                        os.remove(file_name)
                    except:
                        pass


def gunzip_event_files(raw_data_dir):
    files = glob.glob(raw_data_dir + "/*")

    for file_name in files:
        if file_name.endswith('.event.gz'):
            with gzip.open(file_name, 'rb') as f_in:
                with open(file_name.replace('.gz', ''), 'wb') as f_out:
                    try:
                        shutil.copyfileobj(f_in, f_out)
                        os.remove(file_name)
                    except:
                        pass

def main():

    print('Preparing for profiling!')
    # First we do the ROOT setup and loop over the ROOT header/event trees
    init_root()
    root_data_dir = os.environ['BEACON_DATA_DIR']
    root_data_dir += "/../root/"
    root_data_dir += 'run' + str(run)
    event_file = ROOT.TFile(root_data_dir + '/event.root')
    header_file = ROOT.TFile(root_data_dir + '/header.root')
    event_tree = event_file.Get('event')
    header_tree = header_file.Get('header')
    event = ROOT.beacon.Event()
    header = ROOT.beacon.Header()
    event_tree.SetBranchAddress('event',  ROOT.AddressOf(event))
    header_tree.SetBranchAddress('header',  ROOT.AddressOf(header))

    num_loops_over_events = 5
    num_random_accesses = 100
    num_entries = header_tree.GetEntries()

    dd = bt.DataDirectory()
    print('Ready!')
    print('.')
    print('.')
    print('.')


    print('Profiling the ROOT data reading...', end='', flush=True)
    root_seq = []
    root_ra = []
    for i in range(num_loops_over_events):
        read_trees(event_tree, header_tree, num_entries)
        root_seq.append(read_trees.elapsed)
    for j in range(num_random_accesses):
        random_access_trees(event_tree, header_tree, random.randint(0,  num_entries-1))
        root_ra.append(random_access_trees.elapsed)
    print(' Done!')

    # Then before we test the BeaconTau reader we gzip our chosen raw data...
    beacon_data_dir = os.environ['BEACON_DATA_DIR']
    gzip_event_files(beacon_data_dir + '/run' + str(run) + '/event')


    print('Profiling BeaconTau with gzipped data...', end='', flush=True)
    # Now we try reading the gzipped data
    run_analyzer = dd.run(run)

    bt_gzip_seq = []
    bt_gzip_ra = []
    for i in range(num_loops_over_events):
        read_beacon_tau_run(run_analyzer, num_entries)
        bt_gzip_seq.append(read_beacon_tau_run.elapsed)
    for j in range(num_random_accesses):
        random_access_beacon_tau_run(run_analyzer, random.randint(0,  num_entries-1))
        bt_gzip_ra.append(random_access_beacon_tau_run.elapsed)
    del(run_analyzer)
    print(' Done!')


    # Now we un-gzip all the binary data...
    print('Unzipping for second BeaconTau test...', end='', flush=True)
    gunzip_event_files(beacon_data_dir + '/run' + str(run) + '/event')
    print(' Done!')
    run_analyzer = dd.run(run)

    # And time looping over the non-gzipped data
    print('Profiling BeaconTau with non-gzipped data...', end='', flush=True)
    bt_not_gzip_seq = []
    bt_not_gzip_ra = []
    for i in range(num_loops_over_events):
        read_beacon_tau_run(run_analyzer, num_entries)
        bt_not_gzip_seq.append(read_beacon_tau_run.elapsed)
    for j in range(num_random_accesses):
        random_access_beacon_tau_run(run_analyzer, random.randint(0,  num_entries-1))
        bt_not_gzip_ra.append(random_access_beacon_tau_run.elapsed)

    del(run_analyzer)
    print(' Done!')

    # Finally, we tweak the max number of event files allowed in memory and repeated looping over data is very fast.
    # The downside is you use more RAM, hence why this is configurable and set to a (reasonably) low number.
    print('Profiling BeaconTau with non-gzipped data and increased max_files_in_memory...', end='', flush=True)
    run_analyzer = dd.run(run)
    num_files = len(glob.glob(beacon_data_dir + '/run%s'% run + '/event/*'))
    run_analyzer.file_reader.events.max_files_in_memory = num_files

    bt_not_gzip_more_mem_seq = []
    bt_not_gzip_more_mem_ra = []
    for i in range(num_loops_over_events):
        read_beacon_tau_run(run_analyzer, num_entries)
        bt_not_gzip_more_mem_seq.append(read_beacon_tau_run.elapsed)
    for j in range(num_random_accesses):
        random_access_beacon_tau_run(run_analyzer, random.randint(0,  num_entries-1))
        bt_not_gzip_more_mem_ra.append(random_access_beacon_tau_run.elapsed)
    print(' Done!')

    print('Zipping event files back up...', end='', flush=True)
    gzip_event_files(beacon_data_dir + '/run' + str(run) + '/event') # Back to original status
    print(' Done!')




    print('********************************************************')
    print('Profiling summary:')
    print('********************************************************')
    print_summary('ROOT reading all events sequentially', root_seq)
    print_summary('ROOT reading a single random entry', root_ra)
    print('********************************************************')
    print_summary('BeaconTau reading all gzipped data', bt_gzip_seq)
    print_summary('BeaconTau reading a single random gzipped entry', bt_gzip_ra)
    print('********************************************************')
    print_summary('BeaconTau reading all non-gzipped data', bt_not_gzip_seq)
    print_summary('BeaconTau reading a single random non-gzipped entry', bt_not_gzip_ra)
    print('********************************************************')
    print_summary('BeaconTau reading all non-gzipped data (with large max_files_in_memory)', bt_not_gzip_more_mem_seq)
    print_summary('BeaconTau reading a single random non-gzipped entry (with large max_files_in_memory)', bt_not_gzip_more_mem_ra)
    print('********************************************************')


main()

import ROOT
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
def read_tree(tree):
    """Assumes you've set the branch address already"""

    n = tree.GetEntries()
    print('There are %d entries in TTree::%s' % (n, tree.GetName()))
    for entry in range(n):
        tree.GetEntry(entry)

@time_me
def init_beacontau():
    dd = bt.DataDirectory()
    ra = dd.run(run)
    return ra

@time_me
def read_beacon_tau_run(run_analyzer):
    count = 0
    for event_analyer in run_analyzer.events():
        count += 1

    print('There are %d entries in %s' % (count, repr(run_analyzer)))
def main():

    init_root()
    root_data_dir = os.environ['BEACON_DATA_DIR']
    root_data_dir += "/../root/"
    root_data_dir += 'run' + str(run)  + '/'
    f = ROOT.TFile(root_data_dir + 'event.root')
    t = f.Get('event')
    event = ROOT.beacon.Event()
    t.SetBranchAddress('event',  ROOT.AddressOf(event))


    num_times = 3
    for i in range(num_times):
        read_tree(t)


    run_analyzer = init_beacontau()

    for j in range(num_times):
        read_beacon_tau_run(run_analyzer)


main()

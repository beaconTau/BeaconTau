try:
    from setuptools import setup, Extension
    # Required for compatibility with pip (issue #177)
    from setuptools.command.install import install
except ImportError:
    from distutils.core import setup, Extension
    from distutils.command.install import install

from distutils.command.build import build
from distutils.command.clean import clean

import subprocess
import tempfile
import os

import re

libbeacon_version_tag = "Unknown"
with open('BeaconTau/__init__.py') as version_file:
    for line in version_file:
        if '__version__' in line:
            libbeacon_version_tag = line[:-1].replace('__version__ = ', '').replace('\"', '', 2)
            print(libbeacon_version_tag)
            break

# Try this first?
subprocess.call(["python3", "-m", "install", "pybind11"])
try:
    import pybind11
except ImportError:
    print('***************************************************************')
    print('Error! pybind11 is required to compile the BeaconTau back end.')
    print('Try the following if you have a conda installation:')
    print('')
    print('  $ conda install pybind11')
    print('')
    print("or if you're using a virtualenv:")
    print('')
    print('  $ python3 -m pip install pybind11')
    print('')
    print('Once pybind11 is installed, try installing BeaconTau again.')
    print('***************************************************************')
    exit(1)

pybind11_include_dir = pybind11.get_include()
libbeacon_dir = tempfile.TemporaryDirectory()


class BeaconTauClean(clean):
    description = 'Custom cleanup for the BeaconTau package'
    def run(self):
        libbeacon_dir.cleanup()
        clean.run(self)

class BeaconTauBuild(build):
    description = 'Custom build command for the BeaconTau package.'

    def run(self):
        # Clone and build the required version of libbeacon.so
        clone_command = "git clone --branch v"+ libbeacon_version_tag + " https://github.com/beaconTau/libbeacon " + libbeacon_dir.name
        clone_process = subprocess.Popen(clone_command, shell=True)
        clone_process.wait()
        if clone_process.returncode is not 0:
            raise Exception('Unable to get ' + libbeacon_version_tag +  ' of libbeacon. Aborting!')

        make_beacon_o_command = 'make -f ' + libbeacon_dir.name + '/Makefile -C ' + libbeacon_dir.name + ' beacon.o'
        make_beacon_o_process = subprocess.Popen(make_beacon_o_command, shell=True)
        make_beacon_o_process.wait()
        if make_beacon_o_process.returncode is not 0:
            raise Exception('Unable to build version ' + libbeacon_version_tag + ' of libbeacon. Aborting!')

        # Then do the normal python building
        build.run(self)

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="BeaconTau",
    version=libbeacon_version_tag, # try to keep these in sync
    author="Ben Strutt",
    author_email="strutt@physics.ucla.edu",
    description="A package for interacting with BEACON data in python",
    long_description=long_description,
    license='GPL3',
    url="https://github.com/beaconTau/BeaconTau",
    packages=['BeaconTau'],
    ext_modules=[
        Extension('_BeaconTau', ['FileReader.cpp',  'BeaconTau.cpp'],
                  include_dirs = [libbeacon_dir.name, pybind11_include_dir],
                  library_dirs = ['/usr/local/lib'],
                  libraries=['z'],
                  extra_objects=[libbeacon_dir.name  + '/beacon.o'],
                  extra_compile_args = ['-shared', '-O3', '-Wall', '-fPIC', '-std=c++11'],
                  )
    ],
    install_requires=[
        'pybind11', 'scipy', 'matplotlib', 'bokeh', 'numpy'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX",
    ],
    cmdclass={
        'build' : BeaconTauBuild,
        'clean' : BeaconTauClean,
    }
)


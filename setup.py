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


subprocess.call(["pip", "install", "pybind11"])

import pybind11

pybind11_include_dir = pybind11.get_include()
libbeacon_dir = tempfile.TemporaryDirectory()
libbeacon_version_tag = "0.1.5"


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
    packages=['BeaconTau', 'BeaconTau/Flame'],
    ext_modules=[
        Extension('_BeaconTau', ['BeaconTau.cpp',  libbeacon_dir.name + '/beacon.c'],
                  include_dirs = [libbeacon_dir.name, pybind11_include_dir],
                  library_dirs = ['/usr/local/lib' ],
                  libraries=['z'],
                  extra_compile_args = ['-shared', '-O3', '-Wall', '-std=c++11', '-fPIC'],
                  language = 'c++'
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


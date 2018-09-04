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
import pybind11

pybind11_include_dir = pybind11.get_include()
libnuphase_clone_dir = tempfile.TemporaryDirectory()
libnuphase_version_tag = "0.1.1"


class BeaconTauClean(clean):
    def run(self):
        libnuphase_clone_dir.cleanup()
        clean.run(self)

class BeaconTauBuild(build):
    def run(self):
        # first we clone and build the required version of libnuphase.so
        clone_command = "git clone --branch v"+ libnuphase_version_tag + " https://github.com/beaconTau/libnuphase " + libnuphase_clone_dir.name
        clone_process = subprocess.Popen(clone_command, shell=True)
        clone_process.wait()
        # Then do the normal python building
        build.run(self)


with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="BeaconTau",
    version=libnuphase_version_tag, # try to keep these in sync
    author="Ben Strutt",
    author_email="strutt@physics.ucla.edu",
    description="A package for interacting with BEACON data in python",
    long_description=long_description,
    license='GPL3',
    url="https://github.com/beaconTau/BeaconTau",
    packages=['BeaconTau', 'BeaconTau/Flame'],
    ext_modules=[
        Extension('_BeaconTau', ['BeaconTau.cpp',  libnuphase_clone_dir.name + '/nuphase.c'],
                  include_dirs = [libnuphase_clone_dir.name, pybind11_include_dir],
                  library_dirs = ['/usr/local/lib' ],
                  libraries=['z'],
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

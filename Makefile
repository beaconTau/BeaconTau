BEACON_TAU_VERSION:= $(shell grep '__version__ = ' BeaconTau/__init__.py | sed s,'__version__ = ',,)


##########################################################################################
# Default:
# Runs the python installer from what you have in this directory
# i.e. downloads matched version of libbeacon to a temporary directory,
# compiles it, and grabs the object files it needs, compiles the BeaconTau 
# python bindings and installs them.
##########################################################################################
beacon: 
	@echo "Building BeaconTau v${BEACON_TAU_VERSION}"
	python3 setup.py sdist

	@echo "Installing BeaconTau v${BEACON_TAU_VERSION}"
	python3 -m pip install dist/BeaconTau-${BEACON_TAU_VERSION}.tar.gz


##########################################################################################
# Advanced:
# It is possible to compile BeaconTau against a pre-installed libbeacon
# That's what this command is for.
# It works on my linux laptop and is not guarenteed to work elsewhere.
# You may well need to tweak these flags.
# If your machine is supported on the "standard" installation then see setup.py
# for inspiration on what the correct compiler flags might be.
# Obviously this command does no installation.
# However, importing BeaconTau in this directory will get the correct version.
##########################################################################################

LIBBEACONDIR := ../libbeacon
CXXFLAGS := -O3 -shared -std=c++11 -fPIC
PYBIND11_INCLUDES := `python3 -m pybind11 --includes`
LIB_SUFFIX = `python3-config --extension-suffix`
LIBS := -lstdc++ -lz -lbeacon

devel:
	@echo "Building BeaconTau against "$(LIBBEACONDIR)
	$(CC) $(CXXFLAGS) $(PYBIND11_INCLUDES) -I$(LIBBEACONDIR) -L$(LIBBEACONDIR) $(LIBS) BeaconTau.cpp FileReader.cpp -o _BeaconTau$(LIB_SUFFIX)

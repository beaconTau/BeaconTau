BEACON_TAU_VERSION:= $(shell grep 'libbeacon_version_tag = ' setup.py | sed s,'libbeacon_version_tag = ',,)

LIBBEACONDIR := ../libbeacon
CXXFLAGS := -O3 -shared -std=c++11 -fPIC
PYBIND11_INCLUDES := `python3 -m pybind11 --includes`
LIB_SUFFIX = `python3-config --extension-suffix`

beacon:
	@echo "Building BeaconTau v${BEACON_TAU_VERSION}"
	python setup.py sdist

	@echo "Installing BeaconTau v${BEACON_TAU_VERSION}"
	pip install dist/BeaconTau-${BEACON_TAU_VERSION}.tar.gz

devel:
	@echo "Building BeaconTau against "$(LIBBEACONDIR)
	$(CC) $(CXXFLAGS) $(PYBIND11_INCLUDES) -I$(LIBBEACONDIR) -L$(LIBBEACONDIR) BeaconTau.cpp -o _BeaconTau$(LIB_SUFFIX)

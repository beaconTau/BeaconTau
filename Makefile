BEACON_TAU_VERSION:= $(shell grep 'libbeacon_version_tag = ' setup.py | sed s,'libbeacon_version_tag = ',,)

beacon:
	@echo "Building BeaconTau v${BEACON_TAU_VERSION}"
	python setup.py sdist # Create distribution files
	pip install dist/BeaconTau-${BEACON_TAU_VERSION}.tar.gz # Install distribution locally
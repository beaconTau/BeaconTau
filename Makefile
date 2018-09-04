
NUPHASEDIR=../../libnuphase

all: BEACON

BEACON:
	c++ -O3 -Wall -shared -std=c++11 -fPIC -lz -L${NUPHASEDIR} -lnuphase -I${NUPHASEDIR}  `python3 -m pybind11 --includes` pyBeacon.cpp -o _pyBeacon`python3-config --extension-suffix`

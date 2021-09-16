[![Documentation Status](https://readthedocs.org/projects/rpi-rfm69/badge/?version=latest)](https://rpi-rfm69.readthedocs.io/en/latest/?badge=latest)
[![pylint Status](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/jgillula/385e5dc0d1b4f63dffa3de2db8695a69/raw/test.json)](https://github.com/jgillula/rpi-rfm69/actions/workflows/pylint.yml)
[![Coverage Status](https://coveralls.io/repos/github/jgillula/rpi-rfm69/badge.svg)](https://coveralls.io/github/jgillula/rpi-rfm69)

# RFM69 Radio interface for the Raspberry Pi
This package provides a Python wrapper of the [LowPowerLabs RFM69 library](https://github.com/LowPowerLab/RFM69) and is largely based on the work of [Eric Trombly](https://github.com/etrombly/RFM69) who ported the library from C.

The package expects to be installed on a Raspberry Pi and depends on the [RPI.GPIO](https://pypi.org/project/RPi.GPIO/) and [spidev](https://pypi.org/project/spidev/) libraries. In addition you need to have an RFM69 radio module directly attached to the Pi. 

For details on how to connect such a module and further information regarding the API check out the [documentation](https://rpi-rfm69.readthedocs.io/).

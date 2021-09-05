# rpi-rfm69++
This package is a RFM69 radio interface for the Raspberry Pi. It provides a Python wrapper of the [LowPowerLabs RFM69 library](https://github.com/LowPowerLab/RFM69). It is a fork of 
[Jacob Kittley-Davies' unmaintained repository](https://github.com/jkittley/RFM69), which itself is largely based on the work of [Eric Trombly](https://github.com/etrombly/RFM69) who ported the library from C.

The package expects to be installed on a Raspberry Pi and depends on the [RPI.GPIO](https://pypi.org/project/RPi.GPIO/) and [spidev](https://pypi.org/project/spidev/) libraries. In addition you need to have an RFM69 radio module directly attached to the Pi. 

For details on how to connect such a module and further information regarding the API check out the [documentation](http://rpi-rfm69.readthedocs.io/).

# Differences From [rpi-rfm69](https://github.com/jkittley/RFM69)
This library is intended to be entirely backward-compatible with rpi-rfm69. It also adds the following features:
* Supports ListenModeBurst sending
* Supports callbacks when packets are received

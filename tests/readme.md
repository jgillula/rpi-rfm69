# Testing
Because the library is specifically designed to be tested on a Raspberry Pi we also need to test it on one. To help with this process there is a Fabric script. In addition we need a node with which to interact.


## Setup test node
1. Make sure that you're using the right frequency in ```test-node/test-node.ino```.
2. Make sure to indicate whether or not your transceiver is high power in ```test-node/test-node.ino```.
3. (Optional) If you want to test listenModeSendBurst:
    1. Find the directory that contains ```platform.txt``` for the board you're using. For Arduino IDE 1.5+, it's likely of the form ```$HOME/.arduino15/packages/VENDOR/hardware/ARCH/VERSION_NUM/```, where ```$HOME``` is your home directory, ```VENDOR``` is the board vendor (e.g. ```arduino``` or ```Moteino```), ```ARCH``` is the architecture (e.g. ```avr``` or ```sam```), and ```VERSION_NUM``` is the version of the board definition. For example, for my Moteino the directory was ```$HOME/.arduino15/packages/Moteino/hardware/avr/1.6.1```
    2. In that directory, create a file called ```platform.local.txt``` that contains the single line:
    ```
    compiler.cpp.extra_flags=-DRF69_LISTENMODE_ENABLE
    ```
4. Use the Arduino IDE to upload the sketch: ```test-node/test-node.ino``` to an Adafruit Feather with RFM69, a Moteino, or some other Arduino-based microcontroller with an attached RFM69 radio.

## Setup test environment on remote Raspberry Pi
Inside this directory in a Python 3 environment on your local machine (i.e. not on your Raspberry Pi):
1. (Optional) Setup a virtual environment by running
```
python3 -m venv venv
source venv/bin/activate
```
2. Edit ```config.py``` to choose the right frequency and pins
3. (Optional) If you want to test listenModeSendBurst, uncomment the ```TEST_LISTEN_MODE_SEND_BURST``` flag in ```config.py```
4. Run the following commands (still on your local machine, i.e. not on your Raspberry Pi).
```
pip3 install --upgrade pip
pip3 install -r requirements_local.txt
fab init -H raspberrypi.local 
```
where ```raspberrypi.local``` is the hostname of your Raspberry Pi.

## Run tests on remote environment
From inside your testing environment on your local machine run:
```
fab test -H raspberrypi.local 
```
where ```raspberrypi.local``` is the hostname of your Raspberry Pi.

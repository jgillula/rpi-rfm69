# Testing
Because the library is specifically designed to be tested on a Raspberry Pi we also need to test it on one. To help with this process there is a Fabric script. In addition we need a node with which to interact.


## Setup test node
1. Make sure that you're using the right frequency in [```test-node/test-node.ino```](test-node/test-node.ino).
2. Make sure to indicate whether or not your transceiver is high power in [```test-node/test-node.ino```](test-node/test-node.ino).
3. (Optional) If you want to test listenModeSendBurst:
    1. Find the directory that contains ```platform.txt``` for the board you're using. For Arduino IDE 1.5+, it's likely of the form ```$HOME/.arduino15/packages/VENDOR/hardware/ARCH/VERSION_NUM/```, where ```$HOME``` is your home directory, ```VENDOR``` is the board vendor (e.g. ```arduino``` or ```Moteino```), ```ARCH``` is the architecture (e.g. ```avr``` or ```sam```), and ```VERSION_NUM``` is the version of the board definition. For example, for my Moteino the directory was ```$HOME/.arduino15/packages/Moteino/hardware/avr/1.6.1```
    2. In that directory, create a file called ```platform.local.txt``` that contains the single line:
    ```
    compiler.cpp.extra_flags=-DRF69_LISTENMODE_ENABLE
    ```
4. Use the Arduino IDE to upload the sketch [```test-node/test-node.ino```](test-node/test-node.ino) to an Adafruit Feather with RFM69, a Moteino, or some other Arduino-based microcontroller with an attached RFM69 radio.

## Setup test environment on remote Raspberry Pi
Inside this directory in a Python 3 environment on your local machine (i.e. not on your Raspberry Pi):
1. (Optional) Setup a virtual environment by running
```
python3 -m venv venv_test
source venv_test/bin/activate
```
2. Edit [```test_config.py```](test_config.py) to choose the right frequency and pins
3. (Optional) If you want to test listenModeSendBurst, uncomment the ```TEST_LISTEN_MODE_SEND_BURST``` flag in [```test_config.py```](test_config.py)
4. Run the following commands (still on your local machine, i.e. not on your Raspberry Pi).
```
pip3 install --upgrade pip
pip3 install -r requirements_local.txt
fab -H raspberrypi.local init
```
where ```raspberrypi.local``` is the hostname of your Raspberry Pi.

## Run tests on remote environment
From inside your testing environment on your local machine run:
```
fab -H raspberrypi.local test
```
where ```raspberrypi.local``` is the hostname of your Raspberry Pi.

## Generate and upload test coverage data
1. From inside your testing environment on your local machine run the following line. (This will also run tests first if any relevant files have changed since coverage data was last generated.)
```
fab -H raspberrypi.local coverage
```
2. If your local repo is not on the same commit as the origin repo (i.e. the Github repo) or if you have untracked files, the script will ask you if you still want to proceed. (This is necessary because [coveralls.io](https://coveralls.io/github/jgillula/rpi-rfm69) needs to pull a copy of the repo from Github to show its analysis, and if the local code you're testing is different, the analysis won't match.)
3. Copy the coveralls repo token from [https://coveralls.io/github/jgillula/rpi-rfm69](https://coveralls.io/github/jgillula/rpi-rfm69) and provide it when prompted.

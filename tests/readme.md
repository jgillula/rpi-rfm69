# Testing
Because the library is specifically designed to be tested on a RaspberryPi we also need to test it on one. To help with this process there is a Fabric script. In addition we need a node with which to interact.


## Setup test node
1. Make sure that you're using the right frequency in [```test-node/test-node.ino```](https://github.com/jgillula/rpi-rfm69-plus/blob/0b972c1f468552ac70291cd9ee2f1b8f4b577492/tests/test-node/test-node.ino#L22)
1. Use the Arduino IDE to upload the script: ```test-node/test-node.ino``` to an Adafruit Feather with RFM69, or a Raspberry Pi with an attached [RFM69 bonnet](https://www.adafruit.com/product/4072)


## Setup test environment on remote RaspberryPi
Run the following commands inside a Python 3 environment.

```
pip install -r requirements_local.txt
fab init - H raspberrypi.local 
```

## Run tests on remote environment
From inside your testing environment run:

```
fab test - H raspberrypi.local 
```

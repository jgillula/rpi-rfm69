import pytest
import time
import random
from enum import Enum
from RFM69plus import Radio, RF69_MAX_DATA_LEN
import config

class Mode(Enum):
    NORMAL = 0
    LISTEN = 1

def test_transmit():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
        success = radio.send(2, "Banana", attempts=5, waitTime=100)
        assert success == True

def test_receive():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio: 
        timeout = time.time() + 5
        while time.time() < timeout:
            for packet in radio.get_packets():
                assert packet.data == [ord(x) for x in "Apple\0"]
                return True
            time.sleep(0.1)
        return False
            
def test_txrx():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
        test_message = [random.randint(0,255) for i in range(RF69_MAX_DATA_LEN)]
        success = radio.send(2, test_message, attempts=5, waitTime=100)
        assert success == True
        radio.begin_receive()
        timeout = time.time() + 5
        while (not radio.has_received_packet()) and (time.time() < timeout):
            time.sleep(0.1)
        assert radio.has_received_packet()
        packets = radio.get_packets()
        print(test_message)
        print(packets[0].data)
        assert packets[0].data == [x for x in reversed(test_message)]


def test_listenmodeburst():
    time.sleep(2)
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
        test_message = "listen mode test"#[0] + [random.randint(0,255) for i in range(RF69_MAX_DATA_LEN-1)]
        radio.listenModeSendBurst(2, test_message)
        radio.begin_receive()
        timeout = time.time() + 5
        while (not radio.has_received_packet()) and (time.time() < timeout):
            time.sleep(0.1)
        assert radio.has_received_packet()
        packets = radio.get_packets()
        assert packets[0].data == [ord(x) for x in reversed(test_message)]
#         time.sleep(1)
#         radio.listenModeSendBurst(2, "mode: " + str(Mode.NORMAL.value))
#         time.sleep(1)


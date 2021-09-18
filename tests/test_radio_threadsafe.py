# pylint: disable=pointless-statement,missing-docstring,undefined-variable

import time
import random
import pytest
from test_config import *
from RFM69 import Radio, RF69_MAX_DATA_LEN


def test_transmit_threadsafe():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
        # Test getting a packet when we shouldn't have one
        packet = radio.get_packet(block=False)
        assert packet is None
        # Then test sending a packet
        success = radio.send(2, "Banana", attempts=5, waitTime=1000)
        assert success is True

def test_receive_threadsafe():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
        packet = radio.get_packet(timeout=5)
        if packet:
            assert packet.data == [ord(x) for x in "Apple\0"]
            return True
        return False

def test_txrx_threadsafe():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
        # We'll try sending too big a packet to get some code coverage
        test_message = [random.randint(0, 255) for i in range(RF69_MAX_DATA_LEN+10)]
        success = radio.send(2, test_message, attempts=5, waitTime=100)
        assert success is True
        # If we sleep for one second, the packet should already be there so we can get more code coverage in testing
        time.sleep(1)
        packet = radio.get_packet(timeout=5)
        assert packet is not None
        assert packet.data == list(reversed(test_message[0:RF69_MAX_DATA_LEN]))


def test_listen_mode_send_burst_threadsafe():
    try:
        TEST_LISTEN_MODE_SEND_BURST
        with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
            # Try sending bytes instead of a string to get more test coverage
            test_message = [108, 105, 115, 116, 101, 110, 32, 109, 111, 100, 101, 32, 116, 101, 115, 116] # this corresponds to the string "listen mode test"
            radio.listen_mode_send_burst(2, test_message)
            radio.begin_receive()
            packet = radio.get_packet(timeout=5)
            assert packet is not None
            assert packet.data == list(reversed(test_message))
    except NameError:
        print("Skipping testing listen_mode_send_burst")
        pytest.skip("Skipping testing listen_mode_send_burst since it's not set up")

# pylint: disable=pointless-statement,missing-docstring,protected-access,undefined-variable

import time
import random
import pytest
import RPi.GPIO as GPIO # pylint: disable=consider-using-from-import
from test_config import *
from RFM69 import Radio, RF69_MAX_DATA_LEN


def test_transmit():
    with Radio(FREQUENCY, 1, 99, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER, encryptionKey="sampleEncryptKey", enableATC=ATC_MODE) as radio:
        # Test setting the network ID to the value we'll actually test with
        radio.set_network(100)
        # Try sending to a node that isn't on, and don't require an ack
        success = radio.send(47, "Not a banana", attempts=1, require_ack=False)
        assert success is None
        # Try sending to a node that isn't on, and require an ack, should return false
        success = radio.send(47, "This should return false", attempts=2, waitTime=10)
        assert success is False
        success = radio.send(2, "Banana", attempts=5, waitTime=100)
        assert success is True

def test_receive():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER, encryptionKey="sampleEncryptKey", enableATC=ATC_MODE) as radio:
        timeout = time.time() + 5
        while time.time() < timeout:
            if radio.num_packets() > 0:
                for packet in radio.get_packets():
                    assert packet.data == [ord(x) for x in "Apple\0"]
                    time.sleep(1.0)
                    return True
            time.sleep(0.01)
        return False

def do_txrx_test(radio):
    test_message = [random.randint(0, 255) for i in range(RF69_MAX_DATA_LEN)]
    success = radio.send(2, test_message, attempts=5, waitTime=100)
    assert success is True
    timeout = time.time() + 5
    while (not radio.has_received_packet()) and (time.time() < timeout):
        time.sleep(0.01)
    assert radio.has_received_packet()
    packets = radio.get_packets()
    assert packets[0].data == list(reversed(test_message))
    time.sleep(1.0)

def test_txrx():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER, encryptionKey="sampleEncryptKey", enableATC=ATC_MODE) as radio:
        do_txrx_test(radio)

def test_bcm_pin_numbers():
    # For more test coverage, we'll test this using BCM pin numbers
    # To do that, we have to cleanup the entire GPIO object first
    GPIO.setwarnings(False)
    GPIO.cleanup()
    # The format of this dict is (Raspberry Pi pin number: GPIO number)
    board_to_bcm_map = {3: 2, 5: 3, 7: 4, 8: 14, 10: 15, 11: 17, 12: 18, 13: 27, 15: 22, 16: 23, 18: 24, 19: 10, 21: 9, 22: 25, 23: 11, 24: 8, 26: 7, 27: 0, 28: 1, 29: 5, 31: 6, 32: 12, 33: 13, 35: 19, 36: 16, 37: 26, 38: 20, 40: 21}
    with Radio(FREQUENCY, 1, 100, verbose=True, use_board_pin_numbers=False, interruptPin=board_to_bcm_map[INTERRUPT_PIN], resetPin=board_to_bcm_map[RESET_PIN], spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER, encryptionKey="sampleEncryptKey", enableATC=ATC_MODE) as radio:
        do_txrx_test(radio)
    # Since we used BCM pin numbers, we have to clean up all of GPIO again
    GPIO.cleanup()

def test_listen_mode_send_burst():
    try:
        TEST_LISTEN_MODE_SEND_BURST
        with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER, encryptionKey="sampleEncryptKey", enableATC=ATC_MODE) as radio:
            # For more test coverage, let's try setting the listen mode durations outside the acceptable range, like 70 seconds
            radio.listen_mode_set_durations(256, 70000000)
            radio.listen_mode_set_durations(70000000, 1000400)
            # And then let's check and make sure the default values are still being used
            assert radio.listen_mode_get_durations() == (256, 1000400) # These are the default values
            test_message = "listen mode test"
            radio.listen_mode_send_burst(2, test_message)
            timeout = time.time() + 5
            while (not radio.has_received_packet()) and (time.time() < timeout):
                time.sleep(0.01)
            assert radio.has_received_packet()
            packets = radio.get_packets()
            assert packets[0].data == [ord(x) for x in reversed(test_message)]
            time.sleep(1.0)
    except NameError:
        print("Skipping testing listen_mode_send_burst")
        pytest.skip("Skipping testing listen_mode_send_burst since it's not set up")

def test_general():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER, encryptionKey="sampleEncryptKey", enableATC=ATC_MODE) as radio:
        # This is just here for test coverage
        radio._readRSSI(True)
        radio.read_registers()
        # Get more test coverage in _canSend
        radio.sleep()
        assert radio._canSend() is False
        # Put the radio in standby to do more test coverage for _canSend
        radio._setMode(1)
        assert radio._canSend() is True
        radio._setMode(2)

import pytest
import time
import random
from RFM69 import Radio, RF69_MAX_DATA_LEN
from test_config import *

#Possible additional tests:
# broadcast
# send multiple attempts to ensure ack
# send without ack
# fail to get ack
# encrypt
# promiscuous mode

def test_transmit():
    with Radio(FREQUENCY, 1, 99, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
        # Test setting the network ID to the value we'll actually test with
        radio.set_network(100)
        registers = radio.read_registers()
        success = radio.send(2, "Banana", attempts=5, waitTime=100)
        assert success == True
        radio._readRSSI(True)

def test_receive():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio: 
        timeout = time.time() + 5
        while time.time() < timeout:
            if radio.num_packets() > 0:
                for packet in radio.get_packets():
                    assert packet.data == [ord(x) for x in "Apple\0"]
                    time.sleep(1.0)
                    return True
            time.sleep(0.01)
        return False
            
def test_txrx():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
        test_message = [random.randint(0,255) for i in range(RF69_MAX_DATA_LEN)]
        success = radio.send(2, test_message, attempts=5, waitTime=100)
        assert success == True
        timeout = time.time() + 5
        while (not radio.has_received_packet()) and (time.time() < timeout):
            time.sleep(0.01)
        assert radio.has_received_packet()
        packets = radio.get_packets()
        assert packets[0].data == [x for x in reversed(test_message)]
        time.sleep(1.0)


def test_listen_mode_send_burst():
    try:
        TEST_LISTEN_MODE_SEND_BURST
        with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER) as radio:
            test_message = "listen mode test"
            assert radio.listen_mode_get_durations() == (256, 1000400) # These are the default values
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

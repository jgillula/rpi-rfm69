# pylint: disable=protected-access,missing-docstring,undefined-variable

import random
from test_config import *
from RFM69 import Radio, RF69_MAX_DATA_LEN


def test_broadcast_and_promiscuous_mode():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER, encryptionKey="sampleEncryptKey") as radio:
        test_message = [random.randint(0, 255) for i in range(RF69_MAX_DATA_LEN)]
        # first we send the message out to the world
        radio.broadcast(test_message)
        # And we expect to get it back by promiscuous mode
        radio._promiscuous(True)
        packet = radio.get_packet()
        assert packet.data == list(reversed(test_message))
        assert packet.receiver != 1

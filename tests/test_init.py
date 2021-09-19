# pylint: disable=pointless-statement,missing-docstring,undefined-variable

import warnings
import pytest
from test_config import *
from RFM69 import Radio

def test_config_set_up():
    try:
        FREQUENCY
        INTERRUPT_PIN
        RESET_PIN
        SPI_DEVICE
        IS_HIGH_POWER
    except NameError:
        pytest.fail("You must define your radio configuration in tests/test_config.py in order to run the tests")


def test_init_success():
    radio = Radio(FREQUENCY, 1, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE)
    assert isinstance(radio, Radio)

def test_init_bad_interupt():
    with pytest.raises(ValueError) as _:
        Radio(FREQUENCY, 1, interruptPin=0, resetPin=RESET_PIN, spiDevice=SPI_DEVICE)

def test_init_bad_reset():
    with pytest.raises(ValueError) as _:
        Radio(FREQUENCY, 1, resetPin=0, interruptPin=INTERRUPT_PIN, spiDevice=SPI_DEVICE)

def test_init_bad_spi_bus():
    with pytest.raises(IOError) as _:
        Radio(FREQUENCY, 1, spiBus=-1, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE)

def test_init_bad_spi_device():
    with pytest.raises(IOError) as _:
        Radio(FREQUENCY, 1, spiDevice=-1, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN)

def test_deprecation_warnings():
    with Radio(FREQUENCY, 1, 100, verbose=True, interruptPin=INTERRUPT_PIN, resetPin=RESET_PIN, spiDevice=SPI_DEVICE, isHighPower=IS_HIGH_POWER, encryptionKey="sampleEncryptKey") as radio:
        with warnings.catch_warnings(record=True) as w:
            radio.packets
            assert issubclass(w[-1].category, DeprecationWarning)

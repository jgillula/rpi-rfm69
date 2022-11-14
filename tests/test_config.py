# pylint: disable=unused-import,missing-docstring

from RFM69 import FREQ_315MHZ, FREQ_433MHZ, FREQ_868MHZ, FREQ_915MHZ

# You must uncomment one of these for tests to work
# FREQUENCY     = FREQ_315MHZ
# FREQUENCY     = FREQ_433MHZ
# FREQUENCY     = FREQ_868MHZ
# FREQUENCY     = FREQ_915MHZ


# Defaults
# INTERRUPT_PIN = 18
# RESET_PIN     = 29
# SPI_DEVICE    = 0
# IS_HIGH_POWER = True

# Adafruit RFM69HCW Transceiver Radio Bonnet https://www.adafruit.com/product/4072
# INTERRUPT_PIN = 15
# RESET_PIN     = 22
# SPI_DEVICE    = 1
# IS_HIGH_POWER = True

# RaspyRFM http://www.seegel-systeme.de/2015/09/02/ein-funkmodul-fuer-den-raspberry-raspyrfm/
# Module #1 (Single / 1st module on twin/quattro)
# INTERRUPT_PIN = 22
# RESET_PIN     = None
# SPI_DEVICE    = 0
# IS_HIGH_POWER = False

# RaspyRFM http://www.seegel-systeme.de/2015/09/02/ein-funkmodul-fuer-den-raspberry-raspyrfm/
# Module #2 (2nd module on twin)
# INTERRUPT_PIN = 18
# RESET_PIN     = None
# SPI_DEVICE    = 1
# IS_HIGH_POWER = False

# Uncomment to test ListenMode
# TEST_LISTEN_MODE_SEND_BURST = True

# Uncomment to test ATC mode
# ATC_MODE = True

try:
    ATC_MODE
except NameError:
    ATC_MODE = False

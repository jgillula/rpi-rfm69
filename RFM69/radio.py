import time
import logging
import threading
import warnings

import spidev
import RPi.GPIO as GPIO # pylint: disable=consider-using-from-import

from .registers import *
from .packet import Packet
from .config import get_config


class Radio:
    """RFM69 Radio interface for the Raspberry PI.

    An RFM69 module is expected to be connected to the SPI interface
    of the Raspberry Pi. The class is as a context manager so you can
    instantiate it using the 'with' keyword.

    Args:
        freqBand: Frequency band of radio - 315MHz, 868Mhz, 433MHz or 915MHz.
        nodeID (int): The node ID of this device.
        networkID (int): The network ID

    Keyword Args:
        auto_acknowledge (bool): Automatically send acknowledgements
        isHighPower (bool): Is this a high power radio model
        power (int): Power level - a percentage in range 10 to 100.
        use_board_pin_numbers (bool): Use BOARD (not BCM) pin numbers. Defaults to True.
        interruptPin (int): Pin number of interrupt pin. This is a pin index not a GPIO number.
        resetPin (int): Pin number of reset pin. This is a pin index not a GPIO number.
        spiBus (int): SPI bus number.
        spiDevice (int): SPI device number.
        promiscuousMode (bool): Listen to all messages not just those addressed to this node ID.
        encryptionKey (str): 16 character encryption key.
        verbose (bool): Verbose mode - Activates logging to console.
    """

    def __init__(self, freqBand, nodeID, networkID=100, **kwargs):
        self.logger = None
        if kwargs.get('verbose', False):
            self.logger = self._init_log()

        self.auto_acknowledge = kwargs.get('autoAcknowledge', True)
        self.isRFM69HW = kwargs.get('isHighPower', True)
        self._use_board_pin_numbers = kwargs.get('use_board_pin_numbers', True)
        self.intPin = kwargs.get('interruptPin', 18 if self._use_board_pin_numbers else 24)
        self.rstPin = kwargs.get('resetPin', 29 if self._use_board_pin_numbers else 5)
        self.spiBus = kwargs.get('spiBus', 0)
        self.spiDevice = kwargs.get('spiDevice', 0)
        self.promiscuousMode = kwargs.get('promiscuousMode', 0)

        # Thread-safe locks
        self._spiLock = threading.Lock()
        self._sendLock = threading.Condition()
        self._intLock = threading.Lock()
        self._ackLock = threading.Condition()
        self._modeLock = threading.RLock()

        self.mode = ""
        self.mode_name = ""

        self.address = None
        self._networkID = None

        # ListenMode members
        self._isHighSpeed = True
        self._encryptKey = None
        self.listen_mode_set_durations(DEFAULT_LISTEN_RX_US, DEFAULT_LISTEN_IDLE_US)

        self._packets = []
        self._packetLock = threading.Condition()
        # self._packetQueue = queue.Queue()
        self.acks = {}

        self._init_spi()
        self._init_gpio()
        self._initialize(freqBand, nodeID, networkID)

        self._encrypt(kwargs.get('encryptionKey', 0))
        self.set_power_level(kwargs.get('power', 70))


    def _initialize(self, freqBand, nodeID, networkID):
        self._reset_radio()
        self._set_config(get_config(freqBand, networkID))
        self._setHighPower(self.isRFM69HW)
        # Wait for ModeReady
        while (self._readReg(REG_IRQFLAGS1) & RF_IRQFLAGS1_MODEREADY) == 0x00:
            pass

        self._setAddress(nodeID)
        self._freqBand = freqBand
        self._networkID = networkID
        self._init_interrupt()

    def _init_gpio(self):
        if self._use_board_pin_numbers:
            GPIO.setmode(GPIO.BOARD)
        else:
            GPIO.setmode(GPIO.BCM)
        GPIO.setup(self.intPin, GPIO.IN)
        GPIO.setup(self.rstPin, GPIO.OUT)

    def _init_spi(self):
        #initialize SPI
        self.spi = spidev.SpiDev()
        self.spi.open(self.spiBus, self.spiDevice)
        self.spi.max_speed_hz = 4000000

    def _reset_radio(self):
        # Hard reset the RFM module
        GPIO.output(self.rstPin, GPIO.HIGH)
        time.sleep(0.3)
        GPIO.output(self.rstPin, GPIO.LOW)
        time.sleep(0.3)
        #verify chip is syncing?
        start = time.time()
        while self._readReg(REG_SYNCVALUE1) != 0xAA: # pragma: no cover
            self._writeReg(REG_SYNCVALUE1, 0xAA)
            if time.time() - start > 15:
                raise Exception('Failed to sync with radio')
        start = time.time()
        while self._readReg(REG_SYNCVALUE1) != 0x55: # pragma: no cover
            self._writeReg(REG_SYNCVALUE1, 0x55)
            if time.time() - start > 15:
                raise Exception('Failed to sync with radio')

    def _set_config(self, config):
        for value in config.values():
            self._writeReg(value[0], value[1])

    def _init_interrupt(self):
        GPIO.remove_event_detect(self.intPin)
        GPIO.add_event_detect(self.intPin, GPIO.RISING, callback=self._interruptHandler)


    #
    # End of Init
    #

    def __enter__(self):
        """When the context begins"""
        self.read_temperature()
        self.calibrate_radio()
        self.begin_receive()
        return self

    def __exit__(self, *args):
        """When context exits (including when the script is terminated)"""
        self._shutdown()

    def set_frequency(self, FRF): # pragma: no cover
        """Set the radio frequency"""
        self._writeReg(REG_FRFMSB, FRF >> 16)
        self._writeReg(REG_FRFMID, FRF >> 8)
        self._writeReg(REG_FRFLSB, FRF)

    def sleep(self):
        """Put the radio into sleep mode"""
        self._setMode(RF69_MODE_SLEEP)

    def set_network(self, network_id):
        """Set the network ID (sync)

        Args:
            network_id (int): Value between 1 and 254.

        """
        assert isinstance(network_id, int)
        assert network_id > 0 and network_id < 255
        self._networkID = network_id
        self._writeReg(REG_SYNCVALUE2, network_id)

    def set_power_level(self, percent):
        """Set the transmit power level

        Args:
            percent (int): Value between 0 and 100.

        """
        assert isinstance(percent, int) #type(percent) == int
        self.powerLevel = int(round(31 * (percent / 100)))
        self._writeReg(REG_PALEVEL, (self._readReg(REG_PALEVEL) & 0xE0) | self.powerLevel)


    def _send(self, toAddress, buff="", requestACK=False):
        self._writeReg(REG_PACKETCONFIG2,
                       (self._readReg(REG_PACKETCONFIG2) & 0xFB) | RF_PACKET2_RXRESTART)
        now = time.time()
        while (not self._canSend()) and time.time() - now < RF69_CSMA_LIMIT_S:
            pass #self.has_received_packet()
        self._sendFrame(toAddress, buff, requestACK, False)


    def broadcast(self, buff=""):
        """Broadcast a message to network

        Args:
            buff (str): Message buffer to send
        """
        self.send(RF69_BROADCAST_ADDR, buff, attempts=1, require_ack=False)

    def send(self, toAddress, buff="", **kwargs):
        """Send a message

        Args:
            toAddress (int): Recipient node's ID
            buff (str): Message buffer to send

        Keyword Args:
            attempts (int): Number of attempts
            wait (int): Milliseconds to wait for acknowledgement
            require_ack(bool): Require Acknowledgement. If Attempts > 1 this is auto set to True.

        Returns:
            bool: If acknowledgement received or None is no acknowledgement requested
        """
        attempts = kwargs.get('attempts', 3)
        wait_time = kwargs.get('wait', 50)
        require_ack = kwargs.get('require_ack', True)
        if attempts > 1:
            require_ack = True

        for _ in range(0, attempts):
            self._send(toAddress, buff, attempts > 1)

            if not require_ack:
                return None

            with self._ackLock:
                if self._ackLock.wait_for(lambda: self._ACKReceived(toAddress), wait_time/1000):
                    return True

        return False

    def read_temperature(self, calFactor=0):
        """Read the temperature of the radios CMOS chip.

        Args:
            calFactor: Additional correction to corrects the slope, rising temp = rising val

        Returns:
            int: Temperature in centigrade
        """
        self._setMode(RF69_MODE_STANDBY)
        self._writeReg(REG_TEMP1, RF_TEMP1_MEAS_START)
        while self._readReg(REG_TEMP1) & RF_TEMP1_MEAS_RUNNING:
            pass
        # COURSE_TEMP_COEF puts reading in the ballpark, user can add additional correction
        #'complement'corrects the slope, rising temp = rising val
        return (int(~self._readReg(REG_TEMP2)) * -1) + COURSE_TEMP_COEF + calFactor


    def calibrate_radio(self):
        """Calibrate the internal RC oscillator for use in wide temperature variations.

        See RFM69 datasheet section [4.3.5. RC Timer Accuracy] for more information.
        """
        self._writeReg(REG_OSC1, RF_OSC1_RCCAL_START)
        while self._readReg(REG_OSC1) & RF_OSC1_RCCAL_DONE == 0x00:
            pass

    def read_registers(self):
        """Get all register values.

        Returns:
            list: Register values
        """
        results = []
        for address in range(1, 0x50):
            results.append([str(hex(address)), str(bin(self._readReg(address)))])
        return results

    def begin_receive(self):
        """Begin listening for packets"""
        with self._intLock:
            if self._readReg(REG_IRQFLAGS2) & RF_IRQFLAGS2_PAYLOADREADY:
                # avoid RX deadlocks
                self._writeReg(REG_PACKETCONFIG2, (self._readReg(REG_PACKETCONFIG2) & 0xFB) | RF_PACKET2_RXRESTART)
            #set DIO0 to "PAYLOADREADY" in receive mode
            self._writeReg(REG_DIOMAPPING1, RF_DIOMAPPING1_DIO0_01)
            self._setMode(RF69_MODE_RX)

    def has_received_packet(self):
        """Check if packet received

        Returns:
            bool: True if packet has been received
        """
        # return self._packetQueue.qsize() > 0
        with self._packetLock:
            return len(self._packets) > 0

    def get_packets(self):
        """Get newly received packets.

        Returns:
            list: Returns a list of RFM69.Packet objects.
        """
        # packets = []
        # try:
        #     while True:
        #         packets.append(self._packetQueue.get_nowait())
        # except queue.Empty:
        #     pass
        # return packets
        with self._packetLock:
            packets = list(self._packets)
            self._packets = []
            return packets


    def send_ack(self, toAddress, buff=""):
        """Send an acknowledgement packet

        Args:
            toAddress (int): Recipient node's ID

        """
        while not self._canSend():
            pass #self.has_received_packet()
        self._sendFrame(toAddress, buff, False, True)


    # pylint: disable=missing-function-docstring
    @property
    def packets(self):
        warnings.simplefilter("default")
        warnings.warn("The packets property will be deprecated in a future version. Please use get_packets() and num_packets() instead.", DeprecationWarning)
        return self._packets


    def num_packets(self):
        """Returns the number of received packets

        Returns:
            int: Number of packets in the received queue
        """
        # return self._packetQueue.qsize()
        with self._packetLock:
            return len(self._packets)

    def get_packet(self, block=True, timeout=None):
        """Gets a single packet (thread-safe)

        Args:
            block (bool): Block until a packet is available
            timeout (int): Time to wait if blocking. Set to None to wait forever

        Returns:
            Packet: The oldest packet received if available, or None if no packet is available
        """
        # try:
        #     return self._packetQueue.get(block, timeout)
        # except queue.Empty:
        #     return None
        with self._packetLock:
            # Regardless of blocking, if there's a packet available, return it
            if len(self._packets) > 0:
                return self._packets.pop(0)
            # Otherwise, if we're blocking...
            if block:
                # Wait for us to get a packet
                if self._packetLock.wait_for(self.has_received_packet, timeout):
                    # If we didn't timeout, the above is True, so we pop a packet
                    return self._packets.pop(0)

        return None

    #
    # Internal functions
    #

    def _setMode(self, newMode):
        with self._modeLock:
            if newMode == self.mode or newMode not in [RF69_MODE_TX, RF69_MODE_RX, RF69_MODE_SYNTH, RF69_MODE_STANDBY, RF69_MODE_SLEEP]:
                return
            if newMode == RF69_MODE_TX:
                self.mode_name = "TX"
                self._writeReg(REG_OPMODE, (self._readReg(REG_OPMODE) & 0xE3) | RF_OPMODE_TRANSMITTER)
                if self.isRFM69HW:
                    self._setHighPowerRegs(True)
            elif newMode == RF69_MODE_RX:
                self.mode_name = "RX"
                self._writeReg(REG_OPMODE, (self._readReg(REG_OPMODE) & 0xE3) | RF_OPMODE_RECEIVER)
                if self.isRFM69HW:
                    self._setHighPowerRegs(False)
            elif newMode == RF69_MODE_SYNTH:
                self.mode_name = "Synth"
                self._writeReg(REG_OPMODE, (self._readReg(REG_OPMODE) & 0xE3) | RF_OPMODE_SYNTHESIZER)
            elif newMode == RF69_MODE_STANDBY:
                self.mode_name = "Standby"
                self._writeReg(REG_OPMODE, (self._readReg(REG_OPMODE) & 0xE3) | RF_OPMODE_STANDBY)
            elif newMode == RF69_MODE_SLEEP:
                self.mode_name = "Sleep"
                self._writeReg(REG_OPMODE, (self._readReg(REG_OPMODE) & 0xE3) | RF_OPMODE_SLEEP)
            # we are using packet mode, so this check is not really needed
            # but waiting for mode ready is necessary when going from sleep because the FIFO may not be immediately available from previous mode
            while self.mode == RF69_MODE_SLEEP and self._readReg(REG_IRQFLAGS1) & RF_IRQFLAGS1_MODEREADY == 0x00:
                pass

            self.mode = newMode

    def _setAddress(self, addr):
        self.address = addr
        self._writeReg(REG_NODEADRS, self.address)

    def _canSend(self):
        if self.mode == RF69_MODE_STANDBY:
            self.begin_receive()
            return True
        #if signal stronger than -100dBm is detected assume channel activity - removed self.PAYLOADLEN == 0 and
        elif self.mode == RF69_MODE_RX and self._readRSSI() < CSMA_LIMIT:
            self._setMode(RF69_MODE_STANDBY)
            return True
        return False

    def _ACKReceived(self, fromNodeID):
        if fromNodeID in self.acks:
            self.acks.pop(fromNodeID, None)
            return True
        return False

    def _sendFrame(self, toAddress, buff, requestACK, sendACK):
        #turn off receiver to prevent reception while filling fifo
        self._setMode(RF69_MODE_STANDBY)
        #wait for modeReady
        while (self._readReg(REG_IRQFLAGS1) & RF_IRQFLAGS1_MODEREADY) == 0x00:
            pass
        # DIO0 is "Packet Sent"
        self._writeReg(REG_DIOMAPPING1, RF_DIOMAPPING1_DIO0_00)

        if len(buff) > RF69_MAX_DATA_LEN:
            buff = buff[0:RF69_MAX_DATA_LEN]

        ack = 0
        if sendACK:
            ack = 0x80
        elif requestACK:
            ack = 0x40
        with self._spiLock:
            if isinstance(buff, str):
                self.spi.xfer2([REG_FIFO | 0x80, len(buff) + 3, toAddress, self.address, ack] + [int(ord(i)) for i in list(buff)])
            else:
                self.spi.xfer2([REG_FIFO | 0x80, len(buff) + 3, toAddress, self.address, ack] + buff)

        with self._sendLock:
            self._setMode(RF69_MODE_TX)
            self._sendLock.wait(1.0)
        self._setMode(RF69_MODE_RX)

    def _readRSSI(self, forceTrigger=False):
        rssi = 0
        if forceTrigger:
            self._writeReg(REG_RSSICONFIG, RF_RSSI_START)
            while self._readReg(REG_RSSICONFIG) & RF_RSSI_DONE == 0x00:
                pass
        rssi = self._readReg(REG_RSSIVALUE) * -1
        rssi = rssi >> 1
        return rssi

    def _encrypt(self, key):
        self._setMode(RF69_MODE_STANDBY)
        if key != 0 and len(key) == 16:
            self._encryptKey = key
            with self._spiLock:
                self.spi.xfer([REG_AESKEY1 | 0x80] + [int(ord(i)) for i in list(key)])
            self._writeReg(REG_PACKETCONFIG2, (self._readReg(REG_PACKETCONFIG2) & 0xFE) | RF_PACKET2_AES_ON)
        else:
            self._encryptKey = None
            self._writeReg(REG_PACKETCONFIG2, (self._readReg(REG_PACKETCONFIG2) & 0xFE) | RF_PACKET2_AES_OFF)

    def _readReg(self, addr):
        with self._spiLock:
            return self.spi.xfer([addr & 0x7F, 0])[1]

    def _writeReg(self, addr, value):
        with self._spiLock:
            self.spi.xfer([addr | 0x80, value])

    def _promiscuous(self, onOff):
        self.promiscuousMode = onOff

    def _setHighPower(self, onOff):
        if onOff:
            self._writeReg(REG_OCP, RF_OCP_OFF)
            #enable P1 & P2 amplifier stages
            self._writeReg(REG_PALEVEL, (self._readReg(REG_PALEVEL) & 0x1F) | RF_PALEVEL_PA1_ON | RF_PALEVEL_PA2_ON)
        else:
            self._writeReg(REG_OCP, RF_OCP_ON)
            #enable P0 only
            self._writeReg(REG_PALEVEL, RF_PALEVEL_PA0_ON | RF_PALEVEL_PA1_OFF | RF_PALEVEL_PA2_OFF | powerLevel)

    def _setHighPowerRegs(self, onOff):
        if onOff:
            self._writeReg(REG_TESTPA1, 0x5D)
            self._writeReg(REG_TESTPA2, 0x7C)
        else:
            self._writeReg(REG_TESTPA1, 0x55)
            self._writeReg(REG_TESTPA2, 0x70)

    def _shutdown(self):
        """Shutdown the radio.

        Puts the radio to sleep and cleans up the GPIO connections.
        """
        GPIO.remove_event_detect(self.intPin)
        self._modeLock.acquire()
        self._setHighPower(False)
        self.sleep()
        GPIO.cleanup([self.intPin, self.rstPin])
        self._intLock.acquire()
        self._spiLock.acquire()
        self.spi.close()

    def __str__(self): # pragma: no cover
        return "Radio RFM69"

    def __repr__(self): # pragma: no cover
        return "Radio()"

    # pylint: disable=no-self-use
    def _init_log(self):
        logging.basicConfig(level=logging.DEBUG)
        logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(thread)d - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.propagate = False
        return logger

    def _debug(self, *args): # pragma: no cover
        if self.logger is not None:
            self.logger.debug(*args)

    def _error(self, *args): # pragma: no cover
        if self.logger is not None:
            self.logger.error(*args)

    #
    # Radio interrupt handler
    #

    # pylint: disable=unused-argument
    def _interruptHandler(self, pin): # pragma: no cover
        self._intLock.acquire()
        with self._modeLock:
            with self._sendLock:
                self._sendLock.notify_all()

            if self.mode == RF69_MODE_RX and self._readReg(REG_IRQFLAGS2) & RF_IRQFLAGS2_PAYLOADREADY:
                self._setMode(RF69_MODE_STANDBY)

                with self._spiLock:
                    payload_length, target_id, sender_id, CTLbyte = self.spi.xfer2([REG_FIFO & 0x7f, 0, 0, 0, 0])[1:]

                if payload_length > 66:
                    payload_length = 66

                if not (self.promiscuousMode or target_id == self.address or target_id == RF69_BROADCAST_ADDR):
                    self._debug("Ignore Interrupt")
                    self._intLock.release()
                    self.begin_receive()
                    return

                data_length = payload_length - 3
                ack_received = bool(CTLbyte & 0x80)
                ack_requested = bool(CTLbyte & 0x40) and target_id == self.address # Only send back an ack if we're the intended recipient
                with self._spiLock:
                    data = self.spi.xfer2([REG_FIFO & 0x7f] + [0 for i in range(0, data_length)])[1:]
                rssi = self._readRSSI()

                if ack_received:
                    self._debug("Incoming ack from {}".format(sender_id))
                    # Record acknowledgement
                    with self._ackLock:
                        self.acks.setdefault(sender_id, 1)
                        self._ackLock.notify_all()
                elif ack_requested:
                    self._debug("replying to ack request")
                else:
                    self._debug("Other ??")

                # When message received
                if not ack_received:
                    self._debug("Incoming data packet")
                    # self._packetQueue.put(
                    #     Packet(int(target_id), int(sender_id), int(rssi), list(data))
                    # )
                    with self._packetLock:
                        self._packets.append(
                            Packet(int(target_id), int(sender_id), int(rssi), list(data))
                        )
                        self._packetLock.notify_all()

                # Send acknowledgement if needed
                if ack_requested and self.auto_acknowledge:
                    self._debug("Sending an ack")
                    self._intLock.release()
                    self.send_ack(sender_id)
                    self.begin_receive()
                    return

                self._intLock.release()
                self.begin_receive()
                return

        self._intLock.release()


    #
    # ListenMode functions
    #

    def _reinitRadio(self):
        self._initialize(self._freqBand, self.address, self._networkID)
        if self._encryptKey:
            self._encrypt(self._encryptKey) # Restore the encryption key if necessary
        if self._isHighSpeed:
            self._writeReg(REG_LNA, (self._readReg(REG_LNA) & ~0x3) | RF_LNA_GAINSELECT_AUTO)

    def _getUsForResolution(self, resolution):
        if resolution == RF_LISTEN1_RESOL_RX_64 or resolution == RF_LISTEN1_RESOL_IDLE_64:
            return 64
        elif resolution == RF_LISTEN1_RESOL_RX_4100 or resolution == RF_LISTEN1_RESOL_IDLE_4100:
            return 4100
        elif resolution == RF_LISTEN1_RESOL_RX_262000 or resolution == RF_LISTEN1_RESOL_IDLE_262000:
            return 262000

        return 0 # pragma: no cover

    def _getCoefForResolution(self, resolution, duration):
        resolDuration = self._getUsForResolution(resolution)
        result = int(duration / resolDuration)
        # If the next-higher coefficient is closer, use that
        if abs(duration - ((result + 1) * resolDuration)) < abs(duration - (result * resolDuration)):
            return result + 1
        return result

    def _chooseResolutionAndCoef(self, resolutions, duration):
        for resolution in resolutions:
            coef = self._getCoefForResolution(resolution, duration)
            if coef <= 255:
                coefOut = coef
                resolOut = resolution
                return (resolOut, coefOut)
        # out of range
        return (None, None)

    def listen_mode_set_durations(self, rxDuration, idleDuration):
        """Set the duty cycle for listen mode

        The values used may be slightly different to accomodate what
        is allowed by the radio. This function returns the actual
        values used.

        Args:
            rxDuration (int): number of microseconds to be in receive mode
            idleDuration (int): number of microseconds to be sleeping

        Returns:
            (int, int): the actual (rxDuration, idleDuration) used
        """
        rxResolutions = [RF_LISTEN1_RESOL_RX_64, RF_LISTEN1_RESOL_RX_4100, RF_LISTEN1_RESOL_RX_262000]
        idleResolutions = [RF_LISTEN1_RESOL_IDLE_64, RF_LISTEN1_RESOL_IDLE_4100, RF_LISTEN1_RESOL_IDLE_262000]

        (resolOut, coefOut) = self._chooseResolutionAndCoef(rxResolutions, rxDuration)
        if resolOut and coefOut:
            self._rxListenResolution = resolOut
            self._rxListenCoef = coefOut
        else:
            return (None, None)

        (resolOut, coefOut) = self._chooseResolutionAndCoef(idleResolutions, idleDuration)
        if(resolOut and coefOut):
            self._idleListenResolution = resolOut
            self._idleListenCoef = coefOut
        else:
            return (None, None)

        rxDuration = self._getUsForResolution(self._rxListenResolution) * self._rxListenCoef
        idleDuration = self._getUsForResolution(self._idleListenResolution) * self._idleListenCoef
        self._listenCycleDurationUs = rxDuration + idleDuration
        return (rxDuration, idleDuration)

    def listen_mode_get_durations(self):
        rxDuration = self._getUsForResolution(self._rxListenResolution) * self._rxListenCoef
        idleDuration = self._getUsForResolution(self._idleListenResolution) * self._idleListenCoef
        return (rxDuration, idleDuration)

    def _listenModeApplyHighSpeedSettings(self):
        if not self._isHighSpeed:
            return
        self._writeReg(REG_BITRATEMSB, RF_BITRATEMSB_200000)
        self._writeReg(REG_BITRATELSB, RF_BITRATELSB_200000)
        self._writeReg(REG_FDEVMSB, RF_FDEVMSB_100000)
        self._writeReg(REG_FDEVLSB, RF_FDEVLSB_100000)
        self._writeReg(REG_RXBW, RF_RXBW_DCCFREQ_000 | RF_RXBW_MANT_20 | RF_RXBW_EXP_0)


    def listen_mode_send_burst(self, toAddress, buff):
        """Send a message to nodes in listen mode as a burst

        Args:
            toAddress (int): Recipient node's ID
            buff (str): Message buffer to send
        """
        GPIO.remove_event_detect(self.intPin) #        detachInterrupt(_interruptNum)
        self._setMode(RF69_MODE_STANDBY)
        self._writeReg(REG_PACKETCONFIG1, RF_PACKET1_FORMAT_VARIABLE | RF_PACKET1_DCFREE_WHITENING | RF_PACKET1_CRC_ON | RF_PACKET1_CRCAUTOCLEAR_ON)
        self._writeReg(REG_PACKETCONFIG2, RF_PACKET2_RXRESTARTDELAY_NONE | RF_PACKET2_AUTORXRESTART_ON | RF_PACKET2_AES_OFF)
        self._writeReg(REG_SYNCVALUE1, 0x5A)
        self._writeReg(REG_SYNCVALUE2, 0x5A)
        self._listenModeApplyHighSpeedSettings()
        self._writeReg(REG_FRFMSB, self._readReg(REG_FRFMSB) + 1)
        self._writeReg(REG_FRFLSB, self._readReg(REG_FRFLSB))      # MUST write to LSB to affect change!

        cycleDurationMs = int(self._listenCycleDurationUs / 1000)
        timeRemaining = int(cycleDurationMs)

        self._setMode(RF69_MODE_TX)
        startTime = int(time.time() * 1000) #millis()

        while timeRemaining > 0:
            with self._spiLock:
                if isinstance(buff, str):
                    self.spi.xfer2([REG_FIFO | 0x80, len(buff) + 4, toAddress, self.address, timeRemaining & 0xFF, (timeRemaining >> 8) & 0xFF] + [int(ord(i)) for i in list(buff)])
                else:
                    self.spi.xfer2([REG_FIFO | 0x80, len(buff) + 4, toAddress, self.address, timeRemaining & 0xFF, (timeRemaining >> 8) & 0xFF] + buff)

            while (self._readReg(REG_IRQFLAGS2) & RF_IRQFLAGS2_FIFONOTEMPTY) != 0x00:
                pass # make sure packet is sent before putting more into the FIFO
            timeRemaining = cycleDurationMs - (int(time.time()*1000) - startTime)

        self._setMode(RF69_MODE_STANDBY)
        self._reinitRadio()
        self.begin_receive()

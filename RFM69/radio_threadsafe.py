import sys, time, logging, queue, threading
from datetime import datetime
import logging
import spidev
import RPi.GPIO as GPIO
from .registers import *
from .packet import Packet
from .config import get_config
from .radio import Radio

class RadioThreadSafe(Radio):
    """
    Thread-safe version of the :func:`~RFM69.Radio` class.

    This version is identical to :func:`~RFM69.Radio` with the exceptions noted below
    """
    
    def __init__(self, freqBand, nodeID, networkID=100, **kwargs):
        """"""
        self._spiLock = threading.Lock()
        self._sendLock = threading.Condition()
        self._intLock = threading.Lock()
        self._ackLock = threading.Condition()
        self._modeLock = threading.RLock()
        super().__init__(freqBand, nodeID, networkID, **kwargs)
        del self.packets
        del self.sendLock
        del self.intLock
        self._packets = queue.Queue()
        
        
    def _shutdown(self):
        self._modeLock.acquire()
        self._setHighPower(False)
        self.sleep()
        GPIO.cleanup([self.intPin, self.rstPin])
        self._intLock.acquire()
        self._spiLock.acquire()
        self.spi.close()
        

    def begin_receive(self):
        """"""
        with self._intLock:
            if (self._readReg(REG_IRQFLAGS2) & RF_IRQFLAGS2_PAYLOADREADY):
                # avoid RX deadlocks
                self._writeReg(REG_PACKETCONFIG2, (self._readReg(REG_PACKETCONFIG2) & 0xFB) | RF_PACKET2_RXRESTART)
            #set DIO0 to "PAYLOADREADY" in receive mode
            self._writeReg(REG_DIOMAPPING1, RF_DIOMAPPING1_DIO0_01)
            self._setMode(RF69_MODE_RX)
            

    def has_received_packet(self):
        """"""
        return self._packets.qsize() > 0
    
    def num_packets(self):
        """Returns the number of received packets"""
        return self._packets.qsize()

    def get_packet(self, block=True, timeout=None):
        """Gets a single packet (thread-safe)

        Args:
            block (bool): Block until a packet is available
            timeout (int): Time to wait if blocking. Set to None to wait forever

        Returns:
            Packet: The oldest packet received if available, or None if no packet is available
        """
        try:
            return self._packets.get(block, timeout)
        except queue.Empty:
            return None

    def get_packets(self):
        """"""
        # Create packet
        packets = []
        try:
            while True:
                packets.append(self._packets.get_nowait())
        except queue.Empty:
            pass
        return packets

    # 
    # Internal functions
    # 

    def _setMode(self, newMode):
        with self._modeLock:
            if newMode == self.mode:
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
            else:
                self.mode_name = "Unknown"
                return
            # we are using packet mode, so this check is not really needed
            # but waiting for mode ready is necessary when going from sleep because the FIFO may not be immediately available from previous mode
            #while self._readReg(REG_IRQFLAGS1) & RF_IRQFLAGS1_MODEREADY == 0x00:
            #    pass
            while self.mode == RF69_MODE_SLEEP and self._readReg(REG_IRQFLAGS1) & RF_IRQFLAGS1_MODEREADY == 0x00:
                pass

            self.mode = newMode

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

        if (len(buff) > RF69_MAX_DATA_LEN):
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
            result = self._sendLock.wait(1.0)
        self._setMode(RF69_MODE_RX)


    def _encrypt(self, key):
        self._setMode(RF69_MODE_STANDBY)
        if key != 0 and len(key) == 16:
            self._encryptKey = key
            with self._spiLock:
                self.spi.xfer([REG_AESKEY1 | 0x80] + [int(ord(i)) for i in list(key)])
            self._writeReg(REG_PACKETCONFIG2,(self._readReg(REG_PACKETCONFIG2) & 0xFE) | RF_PACKET2_AES_ON)
        else:
            self._encryptKey = None
            self._writeReg(REG_PACKETCONFIG2,(self._readReg(REG_PACKETCONFIG2) & 0xFE) | RF_PACKET2_AES_OFF)

    def _readReg(self, addr):
        with self._spiLock:
            return self.spi.xfer([addr & 0x7F, 0])[1]

    def _writeReg(self, addr, value):
        with self._spiLock:
            self.spi.xfer([addr | 0x80, value])


    # 
    # Radio interrupt handler
    # 

    def _interruptHandler(self, pin):
        self._intLock.acquire()
        with self._modeLock:
            with self._sendLock:
                self._sendLock.notify_all()

            if self.mode == RF69_MODE_RX and self._readReg(REG_IRQFLAGS2) & RF_IRQFLAGS2_PAYLOADREADY:
                self._setMode(RF69_MODE_STANDBY)

                with self._spiLock:
                    payload_length, target_id, sender_id, CTLbyte = self.spi.xfer2([REG_FIFO & 0x7f,0,0,0,0])[1:]
                    
                if payload_length > 66:
                    payload_length = 66

                if not (self.promiscuousMode or target_id == self.address or target_id == RF69_BROADCAST_ADDR):
                    self._debug("Ignore Interrupt")
                    self._intLock.release()
                    self.begin_receive()
                    return

                data_length = payload_length - 3
                ack_received  = bool(CTLbyte & 0x80)
                ack_requested = bool(CTLbyte & 0x40)
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
                    self._packets.put(
                        Packet(int(target_id), int(sender_id), int(rssi), list(data))
                    )

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



    def send(self, toAddress, buff = "", **kwargs):
        """"""
        attempts = kwargs.get('attempts', 3)
        wait_time = kwargs.get('wait', 50)
        require_ack = kwargs.get('require_ack', True)
        if attempts > 1:
            require_ack = True

        for _ in range(0, attempts):
            self._send(toAddress, buff, attempts>0 )

            if not require_ack:
                return None

            with self._ackLock:
                if self._ackLock.wait_for(lambda : self._ACKReceived(toAddress), wait_time/1000):
                    return True
        
        return False


    def listenModeSendBurst(self, toAddress, buff):
        """"""
        GPIO.remove_event_detect(self.intPin) #        detachInterrupt(_interruptNum)
        self._setMode(RF69_MODE_STANDBY)
        self._writeReg(REG_PACKETCONFIG1, RF_PACKET1_FORMAT_VARIABLE | RF_PACKET1_DCFREE_WHITENING | RF_PACKET1_CRC_ON | RF_PACKET1_CRCAUTOCLEAR_ON )
        self._writeReg(REG_PACKETCONFIG2, RF_PACKET2_RXRESTARTDELAY_NONE | RF_PACKET2_AUTORXRESTART_ON | RF_PACKET2_AES_OFF)
        self._writeReg(REG_SYNCVALUE1, 0x5A)
        self._writeReg(REG_SYNCVALUE2, 0x5A)
        self.listenModeApplyHighSpeedSettings()
        self._writeReg(REG_FRFMSB, self._readReg(REG_FRFMSB) + 1)
        self._writeReg(REG_FRFLSB, self._readReg(REG_FRFLSB))      # MUST write to LSB to affect change!
        
        cycleDurationMs = int(self._listenCycleDurationUs / 1000)
        timeRemaining = int(cycleDurationMs)

        self._setMode(RF69_MODE_TX)
        numSent = 0
        startTime = int(time.time() * 1000) #millis()

        while(timeRemaining > 0):
            with self._spiLock:
                if isinstance(buff, str):
                    self.spi.xfer2([REG_FIFO | 0x80, len(buff) + 4, toAddress, self.address, timeRemaining & 0xFF, (timeRemaining >> 8) & 0xFF] + [int(ord(i)) for i in list(buff)])
                else:
                    self.spi.xfer2([REG_FIFO | 0x80, len(buff) + 4, toAddress, self.address, timeRemaining & 0xFF, (timeRemaining >> 8) & 0xFF] + buff)
            
            while ((self._readReg(REG_IRQFLAGS2) & RF_IRQFLAGS2_FIFONOTEMPTY) != 0x00):
                pass # make sure packet is sent before putting more into the FIFO
            timeRemaining = cycleDurationMs - (int(time.time()*1000) - startTime)

        self._setMode(RF69_MODE_STANDBY)
        self._reinitRadio()

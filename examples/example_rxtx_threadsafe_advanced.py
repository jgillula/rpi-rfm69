from RFM69 import RadioThreadSafe
import time
import threading

node_id = 1
network_id = 100
recipient_id = 2

# We'll run this function in a separate thread
def receiveFunction(radio):
    while True:
        # This call will block until a packet is received
        packet = radio.get_packet()
        # Process packet
        print(packet)

# The following are for an Adafruit RFM69HCW Transceiver Radio Bonnet https://www.adafruit.com/product/4072
# You should adjust them to whatever matches your radio
with RadioThreadSafe(FREQ_915MHZ, node_id, network_id, isHighPower=True, verbose=True, interruptPin=15, resetPin=22, spiDevice=1) as radio:
    print ("Starting loop...")

    # Create a thread to run receiveFunction in the background and start it
    receiveThread = threading.Thread(target = receiveFunction, args=(radio))
    receiveThread.start()

    while True:
        # After 5 seconds send a message
        time.sleep(5)
        print ("Sending")
        if radio.send(2, "TEST", attempts=3, waitTime=100):
            print ("Acknowledgement received")
        else:
            print ("No Acknowledgement")
        

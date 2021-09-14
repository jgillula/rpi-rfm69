from RFM69 import Radio
import time

node_id = 1
network_id = 100
recipient_id = 2

# The following are for an Adafruit RFM69HCW Transceiver Radio Bonnet https://www.adafruit.com/product/4072
# You should adjust them to whatever matches your radio
with Radio(FREQ_915MHZ, node_id, network_id, isHighPower=True, verbose=True, interruptPin=15, resetPin=22, spiDevice=1) as radio:
    print ("Starting loop...")
    
    rx_counter = 0
    tx_counter = 0

    while True:
        
        # Every 10 seconds get packets
        if rx_counter > 10:
            rx_counter = 0
            
            # Process packets
            for packet in radio.get_packets():
                print (packet)

        # Every 5 seconds send a message
        if tx_counter > 5:
            tx_counter=0

            # Send
            print ("Sending")
            if radio.send(2, "TEST", attempts=3, waitTime=100):
                print ("Acknowledgement received")
            else:
                print ("No Acknowledgement")


        print("Listening...", len(radio.packets), radio.mode_name)
        delay = 0.5
        rx_counter += delay
        tx_counter += delay
        time.sleep(delay)

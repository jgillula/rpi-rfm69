import pytest
from RFM69 import Packet

def test_packet():
    # Data corresponds to the string "this is a test"
    packet = Packet(1, 2, -10, [116, 104, 105, 115, 32, 105, 115, 32, 97, 32, 116, 101, 115, 116])
    print(packet.to_dict())
    print(packet.to_dict("%b %d %Y %H:%M:%S"))
    assert packet.data_string == "this is a test"
    print(repr(packet))
    print(str(packet))

// **********************************************************************************
//
// Test RFM69 Radio.
//
// **********************************************************************************

#include <RFM69.h>              // https://www.github.com/lowpowerlab/rfm69
#include <RFM69_ATC.h>          // https://www.github.com/lowpowerlab/rfm69
#include <LowPower.h>           // https://github.com/LowPowerLab/LowPower
#include <SPI.h>                // Included with Arduino IDE

// Node and network config
#define NODEID        2    // The ID of this node (must be different for every node on network)
#define NETWORKID     100  // The network ID

// Are you using the RFM69 Wing? Uncomment if you are.
//#define USING_RFM69_WING

// The transmision frequency of the board. Change as needed.
//#define FREQUENCY      RF69_433MHZ
//#define FREQUENCY      RF69_868MHZ
#define FREQUENCY      RF69_915MHZ

// Uncomment if this board is the RFM69HW/HCW not the RFM69W/CW
//#define IS_RFM69HW_HCW

// Serial board rate - just used to print debug messages
#define SERIAL_BAUD   57600

// Board and radio specific config - You should not need to edit
#if defined (__AVR_ATmega32U4__) && defined (USING_RFM69_WING)
#define RF69_SPI_CS  10
#define RF69_RESET   11
#define RF69_IRQ_PIN 2
#elif defined (__AVR_ATmega32U4__)
#define RF69_RESET    4
#define RF69_SPI_CS   8
#define RF69_IRQ_PIN  7
#elif defined(ARDUINO_SAMD_FEATHER_M0) && defined (USING_RFM69_WING)
#define RF69_RESET    11
#define RF69_SPI_CS   10
#define RF69_IRQ_PIN  6
#elif defined(ARDUINO_SAMD_FEATHER_M0)
#define RF69_RESET    4
#define RF69_SPI_CS   8
#define RF69_IRQ_PIN  3
#endif


RFM69 radio(RF69_SPI_CS, RF69_IRQ_PIN, false);

void setup() {
  Serial.begin(SERIAL_BAUD);

  // Initialize the radio
  radio.initialize(FREQUENCY, NODEID, NETWORKID);
#if defined(RF69_LISTENMODE_ENABLE)
  radio.listenModeEnd();
#endif
  radio.spyMode(true);
#ifdef IS_RFM69HW_HCW
  radio.setHighPower(); //must include this only for RFM69HW/HCW!
#endif
  Serial.println("Setup complete");
  Serial.println();
}


// Main loop
unsigned long previousMillis = 0;
const long sendInterval = 3000;
char* data = null;
uint8_t datalen = 0;

void loop() {
  // Receive
  if (radio.receiveDone()) {
    getMessage(data, datalen);
    if (radio.ACKRequested()) {
      radio.sendACK(radio.SENDERID);
    }
    delay(100);
  }


  // Send
  unsigned long currentMillis = millis();
  if (currentMillis - previousMillis >= sendInterval) {
    previousMillis = currentMillis;

    Serial.println("Sending");
    char payload[] = "hello from test node";
    if (radio.sendWithRetry(1, payload, sizeof(payload), 3, 200)) {
      Serial.println("ACK received");
    } else {
      Serial.println("No ACK");
    }
  }
}

bool getMessage(char*& data, uint8_t& datalen) {
  if (data != null) {
    delete data;
    data = null;
  }
  datalen = 0;
  if (radio.DATALEN > 0 && radio.DATA != null) {
    datalen = radio.DATALEN;
    data = new char[datalen];
    memcpy(data, radio.DATA, datalen);
    Serial.println("Received message '" + bufferToString(data, datalen) + "' of length " + String(datalen, DEC));
  }
  return data != null;
}

String bufferToString(char* data, uint8_t datalen) {
  bool all_ascii = true;
  String result = String("");
  for (uint8_t i = 0; i < datalen; i++) all_ascii &= isAscii(data[i]);

  for (uint8_t i = 0; i < datalen; i++) {
    result += all_ascii ? String((char)data[i]) : (String(data[i] < 16 ? "0" : "") + String((uint8_t)data[i], HEX) + String(" "));
  }

  return result;
}

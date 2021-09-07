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
//#define FREQUENCY      RF69_915MHZ

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
  radio.listenModeEnd();
  radio.spyMode(true);
#ifdef IS_RFM69HW_HCW
  radio.setHighPower(); //must include this only for RFM69HW/HCW!
#endif
  Serial.println("Setup complete");
  Serial.println();
}


void loop() {
  // All test names are as named in test_radio.py
  char* data = null; //new char[radio.DATALEN];
  uint8_t datalen = 0;//radio.DATALEN;
  bool success;

  // test_transmit
  Serial.println("----- test_transmit -----");
  while (!radio.receiveDone()) delay(1);
  getMessage(data, datalen);
  if (radio.ACKRequested()) radio.sendACK(radio.SENDERID);
  Serial.println();

  // test_receive
  Serial.println("----- test_receive -----");
  char test_message[] = "Apple";
  delay(3000);
  Serial.print(String("Sending test message '") + test_message + String("' of size ") + String(sizeof(test_message), DEC) + String("..."));
  success = radio.sendWithRetry(1, test_message, sizeof(test_message), 0);
  Serial.println(success ? "Success!" : "Failed");
  Serial.println();

  // test_txrx
  Serial.println("----- test_txrx -----");
  while (!radio.receiveDone()) delay(1);
  getMessage(data, datalen);
  if (radio.ACKRequested()) radio.sendACK(radio.SENDERID);
  char* response = new char[datalen];
  for (uint8_t i = 0; i < datalen; i++) {
    response[i] = data[datalen - i - 1];
  }
  Serial.print("Replying with '" + bufferToString(response, datalen) + "' (length " + String(datalen, DEC) + ")...");
  success = radio.sendWithRetry(1, response, datalen, 0);
  Serial.println(success ? "Success!" : "Failed");
  delete response;
  Serial.println();

  // test_listenmodeburst
  Serial.println("----- test_listenmodeburst -----");
  Serial.println("Entering listen mode");
  Serial.flush();
  delay(500);
  radio.listenModeStart();
  long burst_time_remaining = 0;
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
  if (radio.DATALEN > 0) burst_time_remaining = radio.RF69_LISTEN_BURST_REMAINING_MS;
  getMessage(data, datalen);
  radio.listenModeEnd();
  Serial.flush();
  delay(1000);
  LowPower.longPowerDown(burst_time_remaining);
  response = new char[datalen];
  for (uint8_t i = 0; i < datalen; i++) {
    response[i] = data[datalen - i - 1];
  }
  Serial.print("Replying with '" + bufferToString(response, datalen) + "' (length " + String(datalen, DEC) + ")...");
  success = radio.sendWithRetry(1, response, datalen, 0);
  Serial.println(success ? "Success!" : "Failed");
  delete response;
  Serial.println();
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

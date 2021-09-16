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

#define RUN_TEST(testName, delayTime) runTest(#testName, testName, delayTime) ? numPassed++ : numFailed++;


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
#if defined(RF69_LISTENMODE_ENABLE)
  Serial.println("Note: Tests will include listen_mode_send_burst");
#else
  Serial.println("Note: Skipping testing listenModeSendBurst since it's not set up");
#endif
  Serial.println();
}


char* data = null;
uint8_t datalen = 0;

void loop() {
  Serial.println("Ready to begin tests");
  // All test names are as named in test_radio.py
  bool success;
  uint8_t numPassed = 0;
  uint8_t numFailed = 0;

  RUN_TEST(test_transmit, 0);
  RUN_TEST(test_receive, 1000);
  RUN_TEST(test_txrx, 0);
#if defined(RF69_LISTENMODE_ENABLE)
  RUN_TEST(test_listenModeSendBurst, 0);
#endif

  Serial.println(String("Tests complete: ") + numPassed + String(" passed, ") + numFailed + String(" failed."));
  Serial.println();
}


// **********************************************************************************
// Tests
// **********************************************************************************

bool test_transmit(String& failureReason) {
  bool result = false;
  while (!radio.receiveDone()) delay(1);
  getMessage(data, datalen);
  if (radio.ACKRequested()) {
    radio.sendACK(radio.SENDERID);
    char goal_string[6] = {'B', 'a', 'n', 'a', 'n', 'a'};
    if (datalen >= sizeof(goal_string)) {
      if (strncmp(data, goal_string, 6) == 0) {
        return true;
      } else {
        failureReason = String("Received string '") + String(data) + String("' is not identical to '") + String(goal_string) + String("'");
      }
    } else {
      failureReason = String("Failed! Datalen should have been ") + sizeof("Banana") + String(" but was ") + String(datalen);
    }
  }

  return false;
}

bool test_receive(String& failureReason) {
  char test_message[] = "Apple";
  Serial.println(String("Sending test message '") + test_message + String("' of size ") + String(sizeof(test_message), DEC) + String("..."));
  bool result = radio.sendWithRetry(1, test_message, sizeof(test_message), 5, 1000);
  if (result) {
    return true;
  } else {
    failureReason = String("No ack to our message");
  }

  return false;
}

bool test_txrx(String& failureReason) {
  while (!radio.receiveDone()) delay(1);
  getMessage(data, datalen);
  if (radio.ACKRequested()) radio.sendACK(radio.SENDERID);
  char* response = new char[datalen];
  for (uint8_t i = 0; i < datalen; i++) {
    response[i] = data[datalen - i - 1];
  }
  Serial.println("Replying with '" + bufferToString(response, datalen) + "' (length " + String(datalen, DEC) + ")...");
  delay(100);
  bool result = radio.sendWithRetry(1, response, datalen, 5, 1000);
  if (!result) {
    failureReason = String("No ack to our message");
  }
  delete response;

  return result;
}

bool test_listenModeSendBurst(String& failureReason) {
  Serial.println("Entering listen mode and going to sleep");
  Serial.flush();
  radio.listenModeStart();
  long burst_time_remaining = 0;
  LowPower.powerDown(SLEEP_FOREVER, ADC_OFF, BOD_OFF);
  if (radio.DATALEN > 0) burst_time_remaining = radio.RF69_LISTEN_BURST_REMAINING_MS;
  getMessage(data, datalen);
  radio.listenModeEnd();
  Serial.flush();
  LowPower.longPowerDown(burst_time_remaining);
  char* response = new char[datalen];
  for (uint8_t i = 0; i < datalen; i++) {
    response[i] = data[datalen - i - 1];
  }
  Serial.println("Replying with '" + bufferToString(response, datalen) + "' (length " + String(datalen, DEC) + ")...");
  delay(500);
  bool result = radio.sendWithRetry(1, response, datalen, 5, 1000);
  if (!result) {
    failureReason = String("No ack to our message");
  }
  delete response;

  return result;
}

// **********************************************************************************
// Utility functions
// **********************************************************************************
bool runTest(String testName, bool (*test)(String&), uint32_t delayTime) {
  Serial.println(String("----- ") + testName + String(" -----"));
  if (delayTime > 0) Serial.println(String("Waiting ") + delayTime / 1000.0 + String(" seconds before continuing..."));
  delay(delayTime);
  String failureReason = String();
  bool result = test(failureReason);
  if (!result) {
    Serial.println(String("Failed! ") + failureReason);
  }
  Serial.println();
  return result;
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

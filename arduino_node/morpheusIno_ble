#include <ArduinoBLE.h>
#include <SPI.h>
#include <WiFiNINA.h>

// BLE services
BLEService configService("1801");
BLEStringCharacteristic wifiSSID("0010", BLERead|BLEWrite, 25);
BLEStringCharacteristic wifiPSK("0020", BLERead|BLEWrite, 25);
BLEStringCharacteristic wifiStatus("0030", BLERead | BLENotify, 25);
int status = WL_IDLE_STATUS;

// Other variables
int oldBatteryLevel = 0;  // last battery level reading from analog input
long previousMillis = 0;  // last time the battery level was checked, in ms

void setup() {
  Serial.begin(9600);    // initialize serial communication
  while (!Serial);

  // begin initialization
  if (!BLE.begin()) {
    Serial.println("starting BLE failed!");
    while (1);
  }

  // Setup BLE
  BLE.setLocalName("morpheus");
  BLE.setAdvertisedService(configService);
  configService.addCharacteristic(wifiSSID);
  configService.addCharacteristic(wifiPSK);
  configService.addCharacteristic(wifiStatus);
  BLE.addService(configService);
  wifiSSID.writeValue("");
  wifiPSK.writeValue("");
  wifiStatus.writeValue("Not connected");

  // Assign event handlers
  wifiPSK.setEventHandler(BLEWritten, PSKCharacteristicWritten);

  // check for the WiFi module:
  /*if (WiFi.status() == WL_NO_MODULE) {
    Serial.println("Communication with WiFi module failed!");
    // don't continue
    while (true);
  }*/

  // start advertising
  BLE.advertise();

  Serial.println("Bluetooth device active, waiting for connections...");
}

void loop() {
  // wait for a BLE central
  BLEDevice central = BLE.central();

  // if a central is connected to the peripheral:
  if (central) {
    Serial.print("Connected to central: ");
    // print the central's BT address:
    Serial.println(central.address());
    // turn on the LED to indicate the connection:
    digitalWrite(LED_BUILTIN, HIGH);

    // check the battery level every 200ms
    // while the central is connected:
    while (central.connected()) {
      long currentMillis = millis();
      // if 200ms have passed, check the battery level:
      if (currentMillis - previousMillis >= 200) {
        previousMillis = currentMillis;
      }
    }
    // when the central disconnects, turn off the LED:
    digitalWrite(LED_BUILTIN, LOW);
    Serial.print("Disconnected from central: ");
    Serial.println(central.address());
  }
}

void PSKCharacteristicWritten(BLEDevice central, BLECharacteristic characteristic)
{
  Serial.println("WiFi PSK written");

  if(wifiSSID.value() == "")
  {
    Serial.println("Missing SSID");
    wifiPSK.writeValue("");
  } else {
    // Try connecting to Wifi
    while(status != WL_CONNECTED) {
      Serial.print("Connecting to: ");
      Serial.println(wifiSSID.value());
      status = WiFi.begin(wifiSSID.value().c_str(), wifiPSK.value().c_str());
      delay(10000); 
    }
    Serial.println("Connected");
    printCurrentNet();
  }
}

void printCurrentNet() {
  // print the SSID of the network you're attached to:
  Serial.print("SSID: ");
  Serial.println(WiFi.SSID());

  // print the MAC address of the router you're attached to:
  byte bssid[6];
  WiFi.BSSID(bssid);
  Serial.print("BSSID: ");
  printMacAddress(bssid);

  // print the received signal strength:
  long rssi = WiFi.RSSI();
  Serial.print("signal strength (RSSI):");
  Serial.println(rssi);

  // print the encryption type:
  byte encryption = WiFi.encryptionType();
  Serial.print("Encryption Type:");
  Serial.println(encryption, HEX);
  Serial.println();
}

void printMacAddress(byte mac[]) {
  for (int i = 5; i >= 0; i--) {
    if (mac[i] < 16) {
      Serial.print("0");
    }
    Serial.print(mac[i], HEX);
    if (i > 0) {
      Serial.print(":");
    }
  }
  Serial.println();
}

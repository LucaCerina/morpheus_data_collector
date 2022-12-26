#include <SPI.h>
#include <WiFiNINA.h>
#include <ezTime.h>
#include <Scheduler.h>
#include "secrets.hpp"
#include "wifiUtils.hpp"
#include <ArduinoJson.h>
#include "RestClient.h"
#include "Adafruit_Si7021.h"

// JSON object for authorization
DynamicJsonDocument config(1024);

int status = WL_IDLE_STATUS;

// Rest API configuration
char url_string[] = "api.necstcamp.necst.it";
WiFiSSLClient wificlient;
RestClient client = RestClient(wificlient, url_string, 443);

// Sensors
Adafruit_Si7021 tempSensor = Adafruit_Si7021();

void APIlogin() // TODO pass user and pwd as parameters
{
    // Prepare JSON
    DynamicJsonDocument data(300);
    data["username"] = hwUser;
    data["password"] = hwPsk;
    // Serialize data
    String serData;
    serializeJson(data, serData);
    // Call API
    int status = client.post("/users/login", serData.c_str());
    String response = client.readResponse();
    Serial.println(status);
    if (status == 200)
    {
        DeserializationError error = deserializeJson(data, response);
        if (error)
        {
            config["token"] = "";
        }
        else
        {
            config["token"] = data["token"];
        }
    }
}

void setup()
{
    Serial.begin(9600); // initialize serial communication
    while (!Serial)
        ;

    // Init si7021 sensor
    if (!tempSensor.begin())
    {
        Serial.println("Did not find si7021 sensor");
        while (true)
            ;
    }

    // check for the WiFi module: TODO add external modification of wifi config
    if (WiFi.status() == WL_NO_MODULE)
    {
        Serial.println("Communication with WiFi module failed!");
        // don't continue
        while (true)
            ;
    }

    // Try connecting to Wifi
    while (status != WL_CONNECTED)
    {
        Serial.print("Connecting to: ");
        Serial.println(ssid);
        status = WiFi.begin(ssid.c_str(), psk.c_str());
        delay(10000);
    }
    Serial.println("Connected");
    waitForSync();

    // Setup client
    client.setContentType("application/json");
    // Perform authorization login
    APIlogin();
    config["room_id"] = room_id;

    // Prepare schedules
    Scheduler.startLoop(loopTemperature);
}

void loop()
{
    //printCurrentNet();
    Serial.println("Doing main stuff");
    delay(10000);
}

void loopTemperature()
{
    // Local variables
    DynamicJsonDocument data(1024);
    data["token"] = config["token"];
    data.createNestedObject("input");
    data["input"]["room_id"] = config["room_id"];

    // Time variables
    unsigned long now = WiFi.getTime();

    data["input"]["temperature"] = String(tempSensor.readTemperature());
    data["input"]["humidity"] = String(tempSensor.readHumidity());
    data["input"]["timestamp"] = UTC.dateTime(RFC3339);
    serializeJson(data, Serial);
    delay(30000);
}

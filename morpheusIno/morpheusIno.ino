#include <SPI.h>
#include <WiFiNINA.h>
#include <Scheduler.h>
#include "secrets.hpp"
#include "wifiUtils.hpp"

int status = WL_IDLE_STATUS;

String url_string = "https://api.necstcamp.necst.it";

void setup()
{
    Serial.begin(9600); // initialize serial communication
    while (!Serial)
        ;

    // check for the WiFi module:
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
    printCurrentNet();

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
    Serial.println("Here reading temperature");
    int pingResult = WiFi.ping("api.necstcamp.necst.it");

    if (pingResult >= 0)
    {
        Serial.print("SUCCESS! RTT = ");
        Serial.print(pingResult);
        Serial.println(" ms");
    }
    else
    {
        Serial.print("FAILED! Error code: ");
        Serial.println(pingResult);
    }
    delay(5000);
}

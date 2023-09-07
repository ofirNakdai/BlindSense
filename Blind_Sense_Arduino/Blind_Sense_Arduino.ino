#include <ESP8266WiFi.h>
//#include <WiFiManager.h>
#include <SoftwareSerial.h>
#include <TinyGPS.h>
#include <ESP8266HTTPClient.h>
#include <WiFiClient.h>
#include <string.h>

#include <DNSServer.h>
#include <ESP8266WebServer.h>

#include <Arduino.h>
#include "AudioFileSourceICYStream.h"
#include "AudioFileSourceBuffer.h"
#include "AudioGeneratorMP3.h"
#include "AudioOutputI2SNoDAC.h"



#ifndef STASSID
#define STASSID "realme 7 Pro"
#define STAPSK  "af56c0d4740f"
#endif

//    ~~~~~~~~ GLOBALS ~~~~~~~~

// wifi credentials
const char* ssid = STASSID;
const char* password = STAPSK;

// GPS 
SoftwareSerial gpsSerial(D2, D1);  // RX, TX pins     D2 = GPS TX,  D1 = GPS RX
TinyGPS gps;
float lat = -1;
float lon = -1;


// chip pins
const int trigPin1 = 12; // D6
const int echoPin1 = 14; // D5

const int trigPin2 = D0; // D6
const int echoPin2 = D3; // D5

const int motorPin = D8;
const int button1Pin = D7;
const int button2Pin = D4;

unsigned long pressStartTime = 0;
bool buttonPressed = false;
bool sosSent = false;



//CLIENT ID:
const uint32_t chipId = ESP.getChipId();

// Define maximum distance for triggering the vibration motor (in cm)
const int maxDistance = 50;

// Define variables for ultrasonic sensor
long duration1, duration2;
int distance1, distance2;




double calculate_distance()
{
  // Send ultrasonic signal
  digitalWrite(trigPin1, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin1, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin1, LOW);

   // Receive ultrasonic signal and calculate distance
  duration1 = pulseIn(echoPin1, HIGH);
  distance1 = duration1 * 0.034 / 2;

  // Send ultrasonic signal
  digitalWrite(trigPin2, LOW);
  delayMicroseconds(2);
  digitalWrite(trigPin2, HIGH);
  delayMicroseconds(10);
  digitalWrite(trigPin2, LOW);

   // Receive ultrasonic signal and calculate distance
  duration2 = pulseIn(echoPin2, HIGH);
  distance2 = duration2 * 0.034 / 2;

  if (distance2 <= distance1)
    return distance2;
  else
    return distance1;
}

void turn_on_off_motor(int power)
{
  Serial.print("Power: ");
  Serial.print(power);
  Serial.print("      ");


   if (power == 1)
  {
    digitalWrite(motorPin, HIGH);
  } 
  else
  {
    digitalWrite(motorPin, LOW);
  }
}

void printLocationFromGPS(float* lat_out, float* lon_out)
{
  int printingFlag = 0;
  unsigned long startTime = millis(); // Record the start time
  bool isBreaked = false; 

  while (!printingFlag && !isBreaked)
  {
    while (gpsSerial.available() > 0)
    {
      if (gps.encode(gpsSerial.read()))
      {
        float latitude, longitude;
        gps.f_get_position(lat_out, lon_out);

        Serial.print("Latitude: ");
        Serial.println(*(lat_out), 6);
        Serial.print("Longitude: ");
        Serial.println(*(lon_out), 6);
        printingFlag = 1;
        isBreaked = true;
        // return true;
        break;
      }

          // Check if 2 seconds have passed
    if (millis() - startTime >= 2000)
    {
      // Break the loop if 2 seconds have passed
      isBreaked = true;
      Serial.println("~~~~~~~~~~~~~~~~~~~GPS NOT AVAILABLE~~~~~~~~~~~~~~~~~~~~~~~~");
      Serial.println(*(lon_out), 6);
      Serial.println(*(lat_out), 6);
      // return false;      
      break;
    }
    }


  }
}


void sendHTTP()
{
  printLocationFromGPS(&lat, &lon);

  char URL[216];
  snprintf(URL, sizeof(URL), "http://18.215.158.198:3011/convert?lon=%f&lat=%f&clientID=%u", lon,lat, chipId);// need to fix url
  if(WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;
    WiFiClient client;

    // send http request
    http.begin(client, URL);
    int httpResponseCode = http.GET();

    if(httpResponseCode > 0)
    {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      String payload = http.getString();
      Serial.println(payload);
      
    }
    else
    {
      Serial.print("Error Code:"); 
      Serial.println(httpResponseCode);
    }
    http.end();
  }
  else
  {
    Serial.println("Not Connected to WiFi");
  }
}

void sendSOSHTTP()
{

  printLocationFromGPS(&lat, &lon);

  char URL[216];
  snprintf(URL, sizeof(URL), "http://18.215.158.198:3011/sos?lon=%f&lat=%f&clientID=%u", lon,lat, chipId);// need to fix url
  if(WiFi.status() == WL_CONNECTED)
  {
    HTTPClient http;
    WiFiClient client;

    // send http request
    http.begin(client, URL);
    int httpResponseCode = http.POST("");

    if(httpResponseCode > 0)
    {
      Serial.print("HTTP Response code: ");
      Serial.println(httpResponseCode);
      String payload = http.getString();
      Serial.println(payload);
      
    }
    else
    {
      Serial.print("Error Code:"); 
      Serial.println(httpResponseCode);
    }
    http.end();
  }
  else
  {
    Serial.println("Not Connected to WiFi");
  }
}


//~~~~~~~~~~~~~~~~~~~~~~~ MP3 ~~~~~~~~~~~~~~~~~~~~~~~
const char *URL="http://18.215.158.198:3011/play/output.mp3";// need to fix url

AudioGeneratorMP3 *mp3 = nullptr;
AudioFileSourceICYStream *file = nullptr;
AudioFileSourceBuffer *buff = nullptr;
AudioOutputI2SNoDAC *out = nullptr;

// Called when a metadata event occurs (i.e. an ID3 tag, an ICY block, etc.
void MDCallback(void *cbData, const char *type, bool isUnicode, const char *string)
{
  const char *ptr = reinterpret_cast<const char *>(cbData);
  (void) isUnicode; // Punt this ball for now
  // Note that the type and string may be in PROGMEM, so copy them to RAM for printf
  char s1[32], s2[64];
  strncpy_P(s1, type, sizeof(s1));
  s1[sizeof(s1)-1]=0;
  strncpy_P(s2, string, sizeof(s2));
  s2[sizeof(s2)-1]=0;
  Serial.printf("METADATA(%s) '%s' = '%s'\n", ptr, s1, s2);
  Serial.flush();
}

// Called when there's a warning or error (like a buffer underflow or decode hiccup)
void StatusCallback(void *cbData, int code, const char *string)
{
  const char *ptr = reinterpret_cast<const char *>(cbData);
  // Note that the string may be in PROGMEM, so copy it to RAM for printf
  char s1[64];
  strncpy_P(s1, string, sizeof(s1));
  s1[sizeof(s1)-1]=0;
  Serial.printf("STATUS(%s) '%d' = '%s'\n", ptr, code, s1);
  Serial.flush();
}

// ~~~~~~~~~~~~~~~~~~~~~~~ MP3^ ~~~~~~~~~~~~~~~~~~~~~~~





void setup() {
  Serial.begin(9600);
  gpsSerial.begin(9600);

  Serial.println("Connecting to WiFi");
  WiFi.disconnect();
  WiFi.softAPdisconnect(true);
  WiFi.mode(WIFI_STA);
  
  WiFi.begin(ssid, password);

  // Try forever
  while (WiFi.status() != WL_CONNECTED) {
    Serial.println("...Connecting to WiFi");
    delay(1000);
  }
  Serial.println("Connected");


  //MP3:
  audioLogger = &Serial;

  out = new AudioOutputI2SNoDAC();
  mp3 = new AudioGeneratorMP3();
  mp3->RegisterStatusCB(StatusCallback, (void*)"mp3");


  // pins settup
  pinMode(trigPin1, OUTPUT);
  pinMode(trigPin2, OUTPUT);
  pinMode(echoPin1, INPUT);
  pinMode(echoPin2, INPUT);
  pinMode(motorPin, OUTPUT);
  pinMode(button1Pin, INPUT_PULLUP);
  pinMode(button2Pin, INPUT_PULLUP);
}


void loop() {

  // Send ultrasonic signal
  // Turn on motor if distance is less than maxDistance
  double currDistance = calculate_distance();
  Serial.print("curr: ");
  Serial.print(currDistance);
  Serial.print("        Max: ");
  Serial.print(maxDistance);
  bool difference = currDistance <= maxDistance;
  Serial.print("        ");
  Serial.println(difference);
  
  if( currDistance <= maxDistance)
  {
    turn_on_off_motor(1);
  }
  else
  {
    turn_on_off_motor(0);
  }




  int button1State = digitalRead(button1Pin);  
  if (button1State == LOW) //BUTTON 1 PRESSED
  {
    Serial.println("Button 1 pressed!");
    sendHTTP();

    //MP3:

     // Delete previous instances (if any)
    if (buff != nullptr)
    {
      delete buff;
      buff = nullptr;
    }
    if (file != nullptr)
    {
      delete file;
      file = nullptr;
    }
    if (mp3 != nullptr)
    {
      delete mp3;
      mp3 = nullptr;
    }

    // Create new instances for MP3 playback
    file = new AudioFileSourceICYStream(URL);
    buff = new AudioFileSourceBuffer(file, 2048);
    mp3 = new AudioGeneratorMP3();
    mp3->RegisterStatusCB(StatusCallback, (void*)"mp3");
    mp3->begin(buff, out);

    
    turn_on_off_motor(0);
  } 
  


  bool button2State = digitalRead(button2Pin);
  if (button2State == LOW && !buttonPressed)// BUTTON 2 PRESSED
   {
    // Button was pressed
    Serial.print("Button 2 Pressed!");
    buttonPressed = true;
    pressStartTime = millis();
  }

  if (button2State == HIGH && buttonPressed) // BUTTON 2 RELEASED
  {
    buttonPressed = false;

    unsigned long pressDuration = millis() - pressStartTime;
    Serial.print("time pressed:     ");
    Serial.println(pressDuration);

    if (pressDuration >= 2000) { // Adjust the time threshold as needed
        sendSOSHTTP(); // Call the sendSOS function
    }

  }

  //MP3:
    static int lastms = 0;

  while (mp3->isRunning())
  {
    if (!mp3->loop())
    {
      lastms = 0; //ADDED
      mp3->stop();
    }
  }
}

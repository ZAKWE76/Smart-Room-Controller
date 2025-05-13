// Include necessary libraries
#include <WiFi.h>          // For WiFi connectivity
#include <HTTPClient.h>    // For making HTTP requests
#include <ArduinoJson.h>   // For JSON parsing/creation
#include <ESP32Servo.h>    // For servo control
#include <DHT.h>           // For temperature/humidity sensor

// WiFi network credentials
const char* ssid = "Dinny properties main";  
const char* password = "#Tseleng@1";         

// Flask server configuration
const char* serverUrl = "http://192.168.0.149:5000/esp/update";  // Endpoint for sensor data

// Hardware pin configuration
#define LDR_PIN 39        // Analog pin for Light Dependent Resistor (LDR)
#define PIR_PIN 26        // Digital pin for Passive Infrared (PIR) motion sensor
#define LED_PIN 25        // Digital pin for LED control
#define SERVO_PIN 27      // PWM pin for Servo motor control
#define DHT_PIN 14        // Pin for DHT11 temperature sensor
#define DHT_TYPE DHT11    // Specifying i am using DHT11 sensor

// Threshold values for automatic control
#define LIGHT_THRESHOLD 2000    // If light level < 2000, turn LED on
#define TEMP_THRESHOLD 25.0     // If temp > 25°C and motion detected, turn servo

// Initialize sensor objects
DHT dht(DHT_PIN, DHT_TYPE);  //Temperature sensor
Servo myServo;               // Servo motor controller

// Global variables to store current state
int lightLevel = 0;          // Current light level from LDR
bool motionDetected = false; // Motion detection status
float temperature = 0.0;     // Current temperature
int servoAngle = 0;          // Current servo position (0-180°)
bool ledState = false;       // Current LED state (on/off)
bool autoMode = true;        // Current control mode (auto/manual)

void setup() {
  Serial.begin(115200);  // Start serial communication for debugging
  
  // Initialize hardware pins
  pinMode(LDR_PIN, INPUT);    // Set LDR pin as input
  pinMode(PIR_PIN, INPUT);    // Set PIR pin as input
  pinMode(LED_PIN, OUTPUT);   // Set LED pin as output
  myServo.attach(SERVO_PIN);  // Attach servo to its pin
  dht.begin();                // Initialize temperature sensor
  
  // Connect to WiFi network
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  // Wait for connection
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  // Print connection details
  Serial.println("\nConnected with IP: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  //  Read all sensor values
  readSensors();
  
  //  Automatic control logic (only in auto mode)
  if (autoMode) {
    // LED control: Turn on if light level below threshold
    ledState = (lightLevel < LIGHT_THRESHOLD);
    
    // Servo control: Activate (90°) if motion AND high temperature detected
    servoAngle = (motionDetected && temperature > TEMP_THRESHOLD) ? 90 : 0;
  }
  
  //  Communication with Flask server
  if (WiFi.status() == WL_CONNECTED) {
    // Send sensor data to server
    sendSensorData();
    // Only check for manual updates if not in auto mode
    if (!autoMode) {
      getControlUpdates();
    }
  } else {
    // Handle WiFi disconnection
    Serial.println("WiFi Disconnected");
    WiFi.reconnect();
  }
  
  //  Update physical outputs
  digitalWrite(LED_PIN, ledState ? HIGH : LOW);  // Set LED state
  myServo.write(servoAngle);                     // Move servo to position
  
  delay(2000); // Wait 2 seconds between loops
}

void readSensors() {
  // Read light level from LDR (0-4095, higher = darker)
  lightLevel = analogRead(LDR_PIN);
  
  // Read motion from PIR sensor (HIGH = motion detected)
  motionDetected = digitalRead(PIR_PIN) == HIGH;
  
  // Read temperature from DHT11
  float newTemp = dht.readTemperature();
  // Only update if reading is valid
  if (!isnan(newTemp)) {
    temperature = newTemp;
  }
  
  // Print all sensor readings to serial monitor
  Serial.print("Light: ");
  Serial.print(lightLevel);
  Serial.print(" | Motion: ");
  Serial.print(motionDetected ? "YES" : "NO");
  Serial.print(" | Temp: ");
  Serial.print(temperature);
  Serial.println("°C");
}

void sendSensorData() {
  HTTPClient http;  // Create HTTP client
  
  // Attempt to connect to server
  if (!http.begin(serverUrl)) {
    Serial.println("Failed to connect to server");
    return;
  }
  
  // Set content type header
  http.addHeader("Content-Type", "application/json");
  
  // Create JSON document for sensor data
  DynamicJsonDocument doc(256);
  doc["light_level"] = lightLevel;
  doc["motion_detected"] = motionDetected;
  doc["temperature"] = temperature;
  doc["auto_mode"] = autoMode;  // Include current mode
  
  // Serialize JSON to string
  String payload;
  serializeJson(doc, payload);
  
  // Send POST request with sensor data
  int httpResponseCode = http.POST(payload);
  
  // Process response
  if (httpResponseCode == HTTP_CODE_OK) {
    String response = http.getString();
    DynamicJsonDocument responseDoc(128);
    deserializeJson(responseDoc, response);
    
    // Update auto mode if changed by server
    if (responseDoc.containsKey("auto_mode")) {
      autoMode = responseDoc["auto_mode"];
    }
  } else {
    // Print HTTP error if request failed
    Serial.print("HTTP Error: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();  // Free resources
}

void getControlUpdates() {
  HTTPClient http;
  String url = "http://192.168.0.149:5000/esp/control";
  
  // Attempt to connect to control endpoint
  if (!http.begin(url)) {
    Serial.println("Failed to connect to control endpoint");
    return;
  }
  
  // Send GET request for control updates
  int httpResponseCode = http.GET();
  
  // Process response
  if (httpResponseCode == HTTP_CODE_OK) {
    String response = http.getString();
    DynamicJsonDocument doc(128);
    deserializeJson(doc, response);
    
    // Only update outputs if in manual mode
    if (!autoMode) {
      ledState = doc["led_on"];
      servoAngle = doc["servo_angle"];
    }
    // Always allow auto mode changes
    if (doc.containsKey("auto_mode")) {
      autoMode = doc["auto_mode"];
    }
  } else {
    // Print HTTP error if request failed
    Serial.print("HTTP Error: ");
    Serial.println(httpResponseCode);
  }
  
  http.end();  // Free resources
}
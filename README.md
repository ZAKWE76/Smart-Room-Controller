Smart Room Controller

##  Description

The **Smart Room Controller** is an energy-efficient IoT system that controls room lighting and ventilation based on real-time temperature and motion data. It helps reduce unnecessary electricity consumption by using automated logic and manual overrides through a desktop interface.

This project integrates three main components:

* **ESP32** – Hardware controller for reading sensors and controlling actuators
* **Flask** – Python-based backend server for logic and communication
* **Flet Desktop** – Python frontend for user interaction and control

---

##  ESP32 (Microcontroller)

###  Features

* Reads data from DHT11 (temperature), PIR (motion), and LDR (light) sensors
* Controls LED and servo motor
* Sends sensor data to Flask server via HTTP
* Receives control commands from Flask

###  Requirements

* ESP32 microcontroller board
* Arduino IDE with ESP32 board support installed
* Sensors: DHT11, PIR, LDR
* Actuators: LED, Servo motor (used in place of a fan)
* Wi-Fi connection

###  Setup

1. Connect all sensors and actuators to the ESP32 according to the schematic.
2. Open Arduino IDE and install the required libraries (`DHT`, `WiFi`, `HTTPClient`).
3. Upload the code from `ESP32_code/sketch_may12a.ino` to the ESP32.
4. Ensure ESP32 and PC are on the same Wi-Fi network.

---

##  Flask (Backend Server)

###  Features

* Receives sensor data from ESP32
* Processes automation logic for lighting and ventilation
* Sends control states back to ESP32
* Allows Flet app to update thresholds or override states

###  Requirements

* Python 3.13.2
* Flask
* Flask-CORS

###  Setup

1. Navigate to `flask_app` folder.
2. Install dependencies:

   ```bash
   pip install flask flask-cors
   ```
3. Run the server:

   ```bash
   python backend.py
   ```
4. Make sure it's accessible at `http://192.168.0.149:5000`

---

##  Flet Desktop (Frontend)

### Features

* View real-time data (light, temperature, motion)
* Manually control LED and servo when in manual mode
* Switch between auto/manual modes
* Update threshold values for automation logic

###  Requirements

* Python 3.13.2
* Flet (Python package)

###  Setup

1. Navigate to `Flet_app/Frontend` folder.
2. Install Flet:

   ```bash
   pip install flet
   ```
3. Run the UI:

   ```bash
   python src/main.py
   ```
4. Ensure it connects to the backend at `http://192.168.0.149:5000`

---

##  Schematic

The schematic below shows the wiring and hardware configuration of the Smart Room Controller system. It includes the ESP32 board connected to the following components:

* DHT11 sensor (temperature and humidity)
* PIR motion sensor
* LDR for light detection (with a resistor)
* LED for light output
* Servo motor for ventilation control

![Schematic](https://github.com/user-attachments/assets/e4a1c3e5-1b05-4cff-ba44-920887bbb747)


Make sure to follow this schematic accurately when assembling your hardware.

---

**Author**: Nomcebo Zakwe
**Note**: All devices must be on the same local network to communicate. 


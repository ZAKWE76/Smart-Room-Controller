from flask import Flask, request, jsonify # type: ignore
from flask_cors import CORS # type: ignore

app = Flask(__name__)
CORS(app)

# Global state
initial_state = {
    "light_level": 0,             # from LDR (0-4095)
    "motion_detected": False,     # from PIR
    "temperature": 20.0,          # from DHT11

    "led_on": False,              # LED control
    "servo_angle": 0,             # Servo control
    "auto_mode": True,            # Auto/manual mode

    "temp_threshold": 25.0,       # Trigger temp for servo
    "light_threshold": 2000       # Trigger light for LED
}

@app.route('/esp/update', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.get_json()

        # Update data from esp
        initial_state["light_level"] = data.get("light_level", initial_state["light_level"]) #update the ESP light level of LDR
        initial_state["motion_detected"] = data.get("motion_detected", initial_state["motion_detected"]) #update the ESP motion status
        initial_state["temperature"] = data.get("temperature", initial_state["temperature"]) #update the ESP temperature
        initial_state["auto_mode"] = data.get("auto_mode", initial_state["auto_mode"]) #update the current mode

        # only control the led, servo, and pir sensor automatically if in auto mode
        if initial_state["auto_mode"]:
            initial_state["led_on"] = initial_state["light_level"] < initial_state["light_threshold"]
            if initial_state["motion_detected"] and initial_state["temperature"] > initial_state["temp_threshold"]:
                initial_state["servo_angle"] = 90 #turn servo(fan) ON if the temperature is above the threshold temperature
            else:
                initial_state["servo_angle"] = 0

        # update JSON file
        return jsonify({
            "status": "ESP data received successfully",
            "auto_mode": initial_state["auto_mode"],
            "led_on": initial_state["led_on"],
            "servo_angle": initial_state["servo_angle"]
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/esp/control', methods=['GET']) #ESP fetches the default state from the server
def send_to_esp():
    return jsonify(initial_state)

#update flet data
@app.route('/flet/update', methods=['POST'])
def update_controls():
    try:
        data = request.get_json()

        if 'auto_mode' in data:   #Check and update the the mode
            initial_state['auto_mode'] = bool(data['auto_mode'])

        #flet should only control the LED and servo if in manual mode
        if not initial_state['auto_mode']:        
            if 'led_on' in data:   #if in manual mode, control the LED
                initial_state['led_on'] = bool(data['led_on'])
            if 'servo_angle' in data:
                angle = int(data['servo_angle'])
                initial_state['servo_angle'] = max(0, min(180, angle))

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


#get the data from the server and display on the dashboard
@app.route('/api/control_status', methods=['GET'])
def control_status():
    
    return jsonify({
        "auto_mode": initial_state["auto_mode"],
        "led_on": initial_state["led_on"],
        "servo_angle": initial_state["servo_angle"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

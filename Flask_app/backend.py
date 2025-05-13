from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Global state
system_state = {
    "light_level": 0,             # from LDR (0-4095)
    "motion_detected": False,     # from PIR
    "temperature": 25.0,          # from DHT11

    "led_on": False,              # LED control
    "servo_angle": 0,             # Servo control
    "auto_mode": True,            # Auto/manual mode

    "temp_threshold": 28.0,       # Trigger temp for servo
    "light_threshold": 2000       # Trigger light for LED
}

@app.route('/api/sensor_data', methods=['POST'])
def receive_sensor_data():
    try:
        data = request.get_json()

        # Update sensors
        system_state["light_level"] = data.get("light_level", system_state["light_level"])
        system_state["motion_detected"] = data.get("motion_detected", system_state["motion_detected"])
        system_state["temperature"] = data.get("temperature", system_state["temperature"])
        system_state["auto_mode"] = data.get("auto_mode", system_state["auto_mode"])

        # Auto control logic
        if system_state["auto_mode"]:
            system_state["led_on"] = system_state["light_level"] < system_state["light_threshold"]
            if system_state["motion_detected"] and system_state["temperature"] > system_state["temp_threshold"]:
                system_state["servo_angle"] = 90
            else:
                system_state["servo_angle"] = 0

        # Send flat JSON response (easy for ESP)
        return jsonify({
            "status": "success",
            "auto_mode": system_state["auto_mode"],
            "led_on": system_state["led_on"],
            "servo_angle": system_state["servo_angle"]
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/system_state', methods=['GET'])
def get_system_state():
    return jsonify(system_state)

@app.route('/api/update_controls', methods=['POST'])
def update_controls():
    try:
        data = request.get_json()

        if 'auto_mode' in data:
            system_state['auto_mode'] = bool(data['auto_mode'])

        if not system_state['auto_mode']:
            if 'led_on' in data:
                system_state['led_on'] = bool(data['led_on'])
            if 'servo_angle' in data:
                angle = int(data['servo_angle'])
                system_state['servo_angle'] = max(0, min(180, angle))

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/update_thresholds', methods=['POST'])
def update_thresholds():
    try:
        data = request.get_json()

        if 'temp_threshold' in data:
            system_state['temp_threshold'] = float(data['temp_threshold'])
        if 'light_threshold' in data:
            system_state['light_threshold'] = int(data['light_threshold'])

        return jsonify({"status": "success"})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/control_status', methods=['GET'])
def control_status():
    # This is used by ESP in manual mode
    return jsonify({
        "auto_mode": system_state["auto_mode"],
        "led_on": system_state["led_on"],
        "servo_angle": system_state["servo_angle"]
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

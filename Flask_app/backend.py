# Import required Flask modules and other dependencies
from flask import Flask, request, jsonify, Response  # type: ignore
from flask_cors import CORS  # type: ignore

# Create a Flask application instance
app = Flask(__name__)
# Enable CORS (Cross-Origin Resource Sharing) for the app
CORS(app)

# Global state dictionary to store the current system state
initial_state = {
    "light_level": 0,             # Current light level from LDR sensor (0-4095)
    "motion_detected": False,     # Motion detection status from PIR sensor
    "temperature": 20.0,          # Current temperature from DHT11 sensor
    "led_on": False,              # Current state of the LED (on/off)
    "servo_angle": 0,             # Current angle of the servo motor (0-180)
    "auto_mode": True,            # Current operation mode (auto/manual)
    "temp_threshold": 25.0,       # Temperature threshold for servo activation
    "light_threshold": 2000       # Light threshold for LED activation
}

# Define the root route that serves the HTML dashboard
@app.route('/')
def dashboard():
    # Return an HTML response with embedded CSS and JavaScript
    return Response(f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Smart Room Controller Dashboard</title>
        <style>
            /* Basic page styling */
            body {{
                font-family: Arial, sans-serif;
                margin: 20px;
                background-color: #f5f5f5;
            }}
            /* Dashboard container styling */
            .dashboard {{
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            /* Styling for sensor and control sections */
            .sensor-data, .controls {{
                margin-bottom: 20px;
                padding: 15px;
                border: 1px solid #ddd;
                border-radius: 5px;
            }}
            /* Status indicator styling */
            .status {{
                font-weight: bold;
            }}
            /* Color coding for different states */
            .on {{ color: green; }}    /* LED on state */
            .off {{ color: red; }}     /* LED off state */
            .auto {{ color: blue; }}   /* Auto mode */
            .manual {{ color: orange; }} /* Manual mode */
            /* Button styling */
            button {{
                padding: 8px 15px;
                margin: 5px;
                cursor: pointer;
            }}
            /* Threshold control section styling */
            .threshold-control {{
                margin-top: 10px;
            }}
            /* Input field styling */
            input[type="number"] {{
                width: 80px;
                padding: 5px;
            }}
        </style>
    </head>
    <body>
        <!-- Main dashboard container -->
        <div class="dashboard">
            <h1>IoT System Dashboard</h1>
            
            <!-- Sensor readings section -->
            <div class="sensor-data">
                <h2>Sensor Readings</h2>
                <!-- Light level display -->
                <p>Light Level: <span id="light-level">{initial_state["light_level"]}</span></p>
                <!-- Motion detection display -->
                <p>Motion Detected: <span id="motion" class="status">{'YES' if initial_state["motion_detected"] else 'NO'}</span></p>
                <!-- Temperature display -->
                <p>Temperature: <span id="temperature">{initial_state["temperature"]} °C</span></p>
            </div>
            
            <!-- Control status section -->
            <div class="controls">
                <h2>Control Status</h2>
                <!-- Mode display (Auto/Manual) -->
                <p>Mode: <span id="mode" class="status {'auto' if initial_state["auto_mode"] else 'manual'}">
                    {'AUTO' if initial_state["auto_mode"] else 'MANUAL'}
                </span></p>
                <!-- LED status display -->
                <p>LED: <span id="led-status" class="status {'on' if initial_state["led_on"] else 'off'}">
                    {'ON' if initial_state["led_on"] else 'OFF'}
                </span></p>
                <!-- Servo angle display -->
                <p>Servo Angle: <span id="servo-angle">{initial_state["servo_angle"]}°</span></p>
                
                <!-- Threshold settings section -->
                <div class="threshold-control">
                    <h3>Threshold Settings</h3>
                    <!-- Temperature threshold control -->
                    <label>Temperature Threshold (°C): 
                        <input type="number" id="temp-threshold" value="{initial_state["temp_threshold"]}" step="0.1">
                        <button onclick="updateThreshold('temp')">Update</button>
                    </label>
                    <br>
                    <!-- Light threshold control -->
                    <label>Light Threshold: 
                        <input type="number" id="light-threshold" value="{initial_state["light_threshold"]}">
                        <button onclick="updateThreshold('light')">Update</button>
                    </label>
                </div>
            </div>
            
            <!-- Action buttons section -->
            <div class="actions">
                <h2>Actions</h2>
                <!-- Refresh data button -->
                <button onclick="refreshData()">Refresh Data</button>
                <!-- Toggle mode button -->
                <button onclick="toggleAutoMode()">Toggle Auto/Manual</button>
                <!-- Manual controls (only visible in manual mode) -->
                <div id="manual-controls" style="{'display:none;' if initial_state["auto_mode"] else ''}">
                    <button onclick="toggleLED()">Toggle LED</button>
                    <button onclick="setServo(90)">Servo 90°</button>
                    <button onclick="setServo(0)">Servo 0°</button>
                </div>
            </div>
        </div>

        <!-- JavaScript for dynamic functionality -->
        <script>
            // Function to refresh all data from the server
            function refreshData() {{
                fetch('/api/system_status')
                    .then(response => response.json())
                    .then(data => {{
                        // Update all display elements with new data
                        document.getElementById('light-level').textContent = data.light_level;
                        document.getElementById('motion').textContent = data.motion_detected ? 'YES' : 'NO';
                        document.getElementById('temperature').textContent = data.temperature + ' °C';
                        document.getElementById('mode').textContent = data.auto_mode ? 'AUTO' : 'MANUAL';
                        document.getElementById('mode').className = 'status ' + (data.auto_mode ? 'auto' : 'manual');
                        document.getElementById('led-status').textContent = data.led_on ? 'ON' : 'OFF';
                        document.getElementById('led-status').className = 'status ' + (data.led_on ? 'on' : 'off');
                        document.getElementById('servo-angle').textContent = data.servo_angle + '°';
                        document.getElementById('manual-controls').style.display = data.auto_mode ? 'none' : 'block';
                        document.getElementById('temp-threshold').value = data.temp_threshold;
                        document.getElementById('light-threshold').value = data.light_threshold;
                    }});
            }}

            // Function to toggle between auto and manual mode
            function toggleAutoMode() {{
                const newMode = !(document.getElementById('mode').textContent === 'AUTO');
                fetch('/flet/update', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ auto_mode: newMode }})
                }}).then(refreshData);
            }}

            // Function to toggle LED state
            function toggleLED() {{
                const newState = !(document.getElementById('led-status').textContent === 'ON');
                fetch('/flet/update', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ led_on: newState }})
                }}).then(refreshData);
            }}

            // Function to set servo angle
            function setServo(angle) {{
                fetch('/flet/update', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ servo_angle: angle }})
                }}).then(refreshData);
            }}

            // Function to update thresholds
            function updateThreshold(type) {{
                const value = parseFloat(document.getElementById(type + '-threshold').value);
                fetch('/flet/update_thresholds', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ 
                        temp_threshold: type === 'temp' ? value : undefined,
                        light_threshold: type === 'light' ? value : undefined
                    }})
                }}).then(refreshData);
            }}

            // Set up automatic data refresh every 2 seconds
            setInterval(refreshData, 2000);
            
            // Refresh data when page loads
            document.addEventListener('DOMContentLoaded', refreshData);
        </script>
    </body>
    </html>
    """, mimetype='text/html')

# API endpoint for ESP32 to send sensor data
@app.route('/esp/update', methods=['POST'])
def receive_sensor_data():
    try:
        # Get JSON data from the request
        data = request.get_json()
        
        # Update sensor values from ESP32, keeping current values if not provided
        initial_state["light_level"] = data.get("light_level", initial_state["light_level"])
        initial_state["motion_detected"] = data.get("motion_detected", initial_state["motion_detected"])
        initial_state["temperature"] = data.get("temperature", initial_state["temperature"])

        # Automatic control logic (only in auto mode)
        if initial_state["auto_mode"]:
            # Turn LED on if light level below threshold
            initial_state["led_on"] = initial_state["light_level"] < initial_state["light_threshold"]
            # Set servo to 90° if motion detected and temperature above threshold
            if initial_state["motion_detected"] and initial_state["temperature"] > initial_state["temp_threshold"]:
                initial_state["servo_angle"] = 90
            else:
                initial_state["servo_angle"] = 0

        # Return success response with current control states
        return jsonify({
            "status": "success",
            "auto_mode": initial_state["auto_mode"],
            "led_on": initial_state["led_on"],
            "servo_angle": initial_state["servo_angle"]
        })
    except Exception as e:
        # Return error response if something goes wrong
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoint for ESP32 to get current state
@app.route('/esp/control', methods=['GET'])
def send_to_esp():
    # Return the complete system state as JSON
    return jsonify(initial_state)

# API endpoint for frontend to update controls
@app.route('/flet/update', methods=['POST'])
def update_controls():
    try:
        # Get JSON data from the request
        data = request.get_json()
        
        # Update auto mode if provided
        if 'auto_mode' in data:
            initial_state['auto_mode'] = bool(data['auto_mode'])
        
        # Only update LED and servo if in manual mode
        if not initial_state['auto_mode']:
            if 'led_on' in data:
                initial_state['led_on'] = bool(data['led_on'])
            if 'servo_angle' in data:
                # Constrain servo angle between 0 and 180
                angle = int(data['servo_angle'])
                initial_state['servo_angle'] = max(0, min(180, angle))
        
        # Return success response
        return jsonify({"status": "success"})
    except Exception as e:
        # Return error response if something goes wrong
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoint for updating thresholds
@app.route('/flet/update_thresholds', methods=['POST'])
def update_thresholds():
    try:
        # Get JSON data from the request
        data = request.get_json()
        
        # Update temperature threshold if provided
        if 'temp_threshold' in data:
            initial_state['temp_threshold'] = float(data['temp_threshold'])
        
        # Update light threshold if provided
        if 'light_threshold' in data:
            initial_state['light_threshold'] = int(data['light_threshold'])
        
        # Return success response
        return jsonify({"status": "success"})
    except Exception as e:
        # Return error response if something goes wrong
        return jsonify({"status": "error", "message": str(e)}), 500

# API endpoint to get complete system status
@app.route('/api/system_status', methods=['GET'])
def system_status():
    # Return the complete system state as JSON
    return jsonify(initial_state)

# Main entry point for the application
if __name__ == '__main__':
    # Run the Flask app on all network interfaces, port 5000, with debug mode on
    app.run(host='0.0.0.0', port=5000, debug=True)
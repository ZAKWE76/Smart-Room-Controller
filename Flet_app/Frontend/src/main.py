# Import required libraries
import flet as ft  # Flet framework for UI
import requests    # For HTTP requests to backend
import threading   # For running background tasks
import time        # For timing operations

# Configuration constants
BACKEND_URL = "http://192.168.0.149:5000"  # Base URL of Flask backend
REFRESH_INTERVAL = 2  # Seconds between automatic refreshes

def main(page: ft.Page):
    # Configure the main page properties
    page.title = "Smart Room Controller"  # Window title
    page.theme_mode = ft.ThemeMode.LIGHT  # Light theme
    # Center align all content vertically and horizontally
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 20  

    # UI elements for displaying sensor data
    current_light = ft.Text("Light: --")  # Light level display
    current_motion = ft.Text("Motion: --")  # Motion detection display
    current_temp = ft.Text("Temp: -- °C")  # Temperature display
    current_led = ft.Text("LED: --")  # LED state display
    current_servo = ft.Text("Servo: --°")  # Servo angle display
    status_message = ft.Text("", color=ft.Colors.BLUE)  # Status message area

    # control widgets
    auto_switch = ft.Switch(label="Auto Mode", value=True)  # Auto/manual toggle
    # Manual controls (disabled when in auto mode)
    led_switch = ft.Switch(label="Manual LED Control", value=False, disabled=True)
    servo_slider = ft.Slider(min=0, max=180, divisions=180, label="{value}°", disabled=True)

    def update_display(data):
        
        # Update inputs displays
        current_light.value = f"Light: {data.get('light_level', '--')}"
        current_motion.value = f"Motion: {'YES' if data.get('motion_detected') else 'NO'}"
        current_temp.value = f"Temp: {data.get('temperature', '--')} °C"
        # Update output states
        current_led.value = f"LED: {'ON' if data.get('led_on') else 'OFF'}"
        current_servo.value = f"Servo: {data.get('servo_angle', '--')}°"
        
        # Update control widgets
        auto_switch.value = data.get('auto_mode', True)
        led_switch.value = data.get('led_on', False)
        servo_slider.value = data.get('servo_angle', 0)
        
        # Enable/disable manual controls based on current mode
        led_switch.disabled = auto_switch.value
        servo_slider.disabled = auto_switch.value

    def fetch_state():
        #Fetch current state from backend and update UI
        try:
            # Send GET request to backend
            response = requests.get(f"{BACKEND_URL}/esp/control")
            if response.status_code == 200:  # If successful
                update_display(response.json())  # Update UI with new data
                # Update status with current time
                status_message.value = "Last update: " + time.strftime("%H:%M:%S")
            else:
                # Show HTTP error if request failed
                status_message.value = f"Error: {response.status_code}"
        except Exception as e:
            # Show connection errors
            status_message.value = f"Connection error: {str(e)}"
        page.update()  # Refresh the UI

    def update_controls(e):
        #Send control changes to backend
        try:
            # Prepare control data to send
            payload = {
                "auto_mode": auto_switch.value,
                "led_on": led_switch.value,
                "servo_angle": int(servo_slider.value)
            }
            # Send POST request to backend
            response = requests.post(f"{BACKEND_URL}/flet/update", json=payload)
            if response.status_code == 200:
                status_message.value = "Controls updated!"
            else:
                status_message.value = f"Update failed: {response.text}"
        except Exception as e:
            status_message.value = f"Error: {str(e)}"
        page.update()  # Refresh the UI

    def auto_refresh():
        #Background thread to periodically fetch updates
        while True:  # Run continuously
            fetch_state()  # Get latest data
            time.sleep(REFRESH_INTERVAL)  # Wait 2 seconds before next refresh

    # Set up event handlers for control changes
    auto_switch.on_change = update_controls
    led_switch.on_change = update_controls
    servo_slider.on_change = update_controls

    # Build the page layout
    page.add(
        ft.Column([  # Vertical layout
            ft.Text("Smart Room Controller Dashboard", size=24, weight="bold"),
            ft.Divider(),  # Horizontal divider
            
            # First row of sensor displays
            ft.Row([current_light, current_motion, current_temp], spacing=20),
            # Second row of actuator displays
            ft.Row([current_led, current_servo], spacing=20),
            ft.Divider(),
            
            # Control section
            auto_switch,
            led_switch,
            servo_slider,
            ft.ElevatedButton("Update Controls", on_click=update_controls),
            ft.Divider(),
            
            # Status message area
            status_message
        ], spacing=10)  # Space between elements
    )

    # Initial data fetch when app starts
    fetch_state()
    
    # Start background refresh thread (daemon=True stops it when main thread ends)
    threading.Thread(target=auto_refresh, daemon=True).start()

# Launch the application
ft.app(target=main)
import flet as ft
import requests
import threading
import time

BACKEND_URL = "http://192.168.0.149:5000"
REFRESH_INTERVAL = 3  # seconds

def main(page: ft.Page):
    page.title = "Smart Room Controller"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.scroll = ft.ScrollMode.AUTO

    # UI Components
    light_display = ft.Text("Light Level: --", size=16)
    motion_display = ft.Text("Motion: --", size=16)
    temp_display = ft.Text("Temperature: -- °C", size=16)

    auto_mode_switch = ft.Switch(label="Auto Mode", value=True)
    led_toggle = ft.Switch(label="LED ON/OFF", value=False)
    fan_toggle = ft.Switch(label="Fan (Servo) Angle", value=False)

    status_text = ft.Text("Connecting...", color=ft.Colors.BLUE_GREY)

    def update_controls(e=None):
        try:
            payload = {
                "auto_mode": auto_mode_switch.value,
                "led_on": led_toggle.value,
                "servo_angle": 90 if fan_toggle.value else 0
            }
            requests.post(f"{BACKEND_URL}/api/update_controls", json=payload)
        except Exception as ex:
            status_text.value = f"Control update failed: {ex}"
            page.update()

    def refresh_state():
        while True:
            try:
                response = requests.get(f"{BACKEND_URL}/api/system_state")
                if response.ok:
                    data = response.json()
                    light_display.value = f"Light Level: {data['light_level']}"
                    motion_display.value = f"Motion: {'YES' if data['motion_detected'] else 'NO'}"
                    temp_display.value = f"Temperature: {data['temperature']} °C"
                    auto_mode_switch.value = data['auto_mode']
                    led_toggle.value = data['led_on']
                    fan_toggle.value = data['servo_angle'] == 90
                    status_text.value = "Updated successfully"
                else:
                    status_text.value = f"Error: {response.status_code}"
            except Exception as e:
                status_text.value = f"Connection error: {e}"

            page.update()
            time.sleep(REFRESH_INTERVAL)

    # Event Handlers
    auto_mode_switch.on_change = update_controls
    led_toggle.on_change = update_controls
    fan_toggle.on_change = update_controls

    # Layout
    page.add(
        ft.Column([
            ft.Text("Smart Room Dashboard", size=24, weight="bold"),
            light_display,
            motion_display,
            temp_display,
            ft.Divider(),
            auto_mode_switch,
            led_toggle,
            fan_toggle,
            status_text
        ], spacing=20, expand=True)
    )

    # Start background thread for state refresh
    threading.Thread(target=refresh_state, daemon=True).start()

ft.app(target=main)

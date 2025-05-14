import flet as ft
import requests
import threading
import time
from datetime import datetime

# Configuration constants
BACKEND_URL = "http://192.168.0.149:5000"
REFRESH_INTERVAL = 2  # Seconds between automatic refreshes

# Custom color scheme - Using ft.Colors (UPPERCASE)
PRIMARY_COLOR = ft.Colors.BLUE_700
SECONDARY_COLOR = ft.Colors.CYAN_400
BACKGROUND_COLOR = ft.Colors.GREY_50
CARD_COLOR = ft.Colors.WHITE
TEXT_COLOR = ft.Colors.GREY_800

def main(page: ft.Page):
    # Configure the main page properties
    page.title = "Smart Room Controller"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = BACKGROUND_COLOR
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # Status tracking
    last_update_time = None
    connection_status = ft.Text("Connecting...", color=ft.Colors.ORANGE_800)

    # UI elements
    header = ft.Text(
        "Smart Room Controller Dashboard",
        size=28,
        weight=ft.FontWeight.BOLD,
        color=PRIMARY_COLOR,
        text_align=ft.TextAlign.CENTER
    )

    # Sensor data cards
    def create_sensor_card(title, value, icon_name, color):
        return ft.Card(
            elevation=5,
            content=ft.Container(
                width=180,
                padding=15,
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=5,
                    controls=[
                        ft.Icon(name=icon_name, color=color, size=30),
                        ft.Text(title, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
                        ft.Text(value, size=18, weight=ft.FontWeight.W_500, color=TEXT_COLOR),
                    ]
                )
            )
        )

    current_light = create_sensor_card("Light Level", "--", ft.Icons.LIGHTBULB_OUTLINE, SECONDARY_COLOR)
    current_motion = create_sensor_card("Motion", "--", ft.Icons.DIRECTIONS_RUN, SECONDARY_COLOR)
    current_temp = create_sensor_card("Temperature", "--°C", ft.Icons.THERMOSTAT, SECONDARY_COLOR)
    current_led = create_sensor_card("LED Status", "--", ft.Icons.LIGHTBULB, SECONDARY_COLOR)
    current_servo = create_sensor_card("Servo Angle", "--°", ft.Icons.SETTINGS_OUTLINED, SECONDARY_COLOR)

    # Status message
    status_message = ft.Text(
        "", 
        color=ft.Colors.BLUE_700,
        text_align=ft.TextAlign.CENTER,
        italic=True
    )

    # Control switches
    auto_switch = ft.Switch(label="Auto Mode", value=True, active_color=PRIMARY_COLOR)
    led_switch = ft.Switch(label="Manual LED", value=False, disabled=True, active_color=PRIMARY_COLOR)
    servo_slider = ft.Slider(min=0, max=180, divisions=180, label="{value}°", disabled=True, active_color=PRIMARY_COLOR)

    # Update controls function (defined before being referenced)
    def update_controls(e):
        try:
            payload = {
                "auto_mode": auto_switch.value,
                "led_on": led_switch.value,
                "servo_angle": int(servo_slider.value)
            }
            response = requests.post(f"{BACKEND_URL}/flet/update", json=payload, timeout=3)
            if response.status_code == 200:
                status_message.value = "Controls updated!"
                status_message.color = ft.Colors.GREEN_700
                fetch_state()  # Refresh to confirm changes
            else:
                status_message.value = f"Update failed: {response.text}"
                status_message.color = ft.Colors.RED_700
        except Exception as e:
            status_message.value = f"Error: {str(e)}"
            status_message.color = ft.Colors.RED_700
        page.update()

    # Set up event handlers
    auto_switch.on_change = update_controls
    led_switch.on_change = update_controls
    servo_slider.on_change = update_controls

    # Update button (now placed after function definition)
    update_button = ft.ElevatedButton(
        "Update Controls",
        icon=ft.Icons.UPDATE,
        on_click=update_controls,
        bgcolor=PRIMARY_COLOR,
        color=ft.Colors.WHITE,
        elevation=2
    )

    # Control cards (defined after all their components)
    mode_card = ft.Card(
        elevation=3,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("Operation Mode", weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                    ft.Row(
                        controls=[
                            ft.Icon(name=ft.Icons.AUTO_MODE, color=PRIMARY_COLOR),
                            auto_switch
                        ],
                        spacing=10
                    )
                ]
            )
        )
    )

    manual_controls_card = ft.Card(
        elevation=3,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                spacing=15,
                controls=[
                    ft.Text("Manual Controls", weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                    ft.Row(
                        controls=[
                            ft.Icon(name=ft.Icons.LIGHTBULB, color=PRIMARY_COLOR),
                            led_switch
                        ],
                        spacing=10
                    ),
                    ft.Column(
                        spacing=5,
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Icon(name=ft.Icons.SETTINGS, color=PRIMARY_COLOR),
                                    ft.Text("Servo Angle", color=TEXT_COLOR)
                                ],
                                spacing=10
                            ),
                            servo_slider
                        ]
                    ),
                    update_button
                ]
            )
        )
    )

    # Status card
    status_card = ft.Card(
        elevation=3,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                spacing=10,
                controls=[
                    ft.Text("System Status", weight=ft.FontWeight.BOLD, color=PRIMARY_COLOR),
                    connection_status,
                    status_message,
                    ft.Row(
                        controls=[
                            ft.Icon(name=ft.Icons.UPDATE, size=16, color=ft.Colors.GREY_600),
                            ft.Text("Last update: --", color=ft.Colors.GREY_600, size=12)
                        ],
                        spacing=5
                    )
                ]
            )
        )
    )

    def update_display(data):
        """Update all UI elements with new data"""
        current_light.content.content.controls[2].value = f"{data.get('light_level', '--')}"
        current_motion.content.content.controls[2].value = "YES" if data.get('motion_detected') else "NO"
        current_temp.content.content.controls[2].value = f"{data.get('temperature', '--')}°C"
        
        led_status = "ON" if data.get('led_on') else "OFF"
        current_led.content.content.controls[2].value = led_status
        current_led.content.content.controls[0].name = ft.Icons.LIGHTBULB if data.get('led_on') else ft.Icons.LIGHTBULB_OUTLINE
        
        current_servo.content.content.controls[2].value = f"{data.get('servo_angle', '--')}°"
        
        auto_switch.value = data.get('auto_mode', True)
        led_switch.value = data.get('led_on', False)
        servo_slider.value = data.get('servo_angle', 0)
        
        led_switch.disabled = auto_switch.value
        servo_slider.disabled = auto_switch.value
        
        nonlocal last_update_time
        last_update_time = datetime.now()
        connection_status.value = "Connected"
        connection_status.color = ft.Colors.GREEN_700
        status_message.value = f"Last update: {last_update_time.strftime('%H:%M:%S')}"

    def fetch_state():
        try:
            response = requests.get(f"{BACKEND_URL}/esp/control", timeout=3)
            if response.status_code == 200:
                update_display(response.json())
                status_message.value = "Data refreshed successfully"
                status_message.color = ft.Colors.BLUE_700
            else:
                raise Exception(f"HTTP {response.status_code}")
        except Exception as e:
            connection_status.value = f"Connection error: {str(e)}"
            connection_status.color = ft.Colors.RED_700
            status_message.value = "Could not fetch latest data"
            status_message.color = ft.Colors.RED_700
        page.update()

    def auto_refresh():
        while True:
            fetch_state()
            time.sleep(REFRESH_INTERVAL)

    # Build the page layout
    page.add(
        ft.Column([
            header,
            ft.Divider(),
            ft.Row([current_light, current_motion, current_temp], spacing=20),
            ft.Row([current_led, current_servo], spacing=20),
            ft.Divider(),
            mode_card,
            manual_controls_card,
            ft.Divider(),
            status_card
        ], spacing=10)
    )

    # Initial data fetch
    fetch_state()
    
    # Start background refresh thread
    threading.Thread(target=auto_refresh, daemon=True).start()

ft.app(target=main)
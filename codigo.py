
#!/usr/bin/env python3
import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import serial
import bluetooth
import os

# --- CONFIG ---
SENSOR_COUNT = 13
READ_INTERVAL = 0.005  # 200 Hz

# --- I2C SETUP ---
i2c = busio.I2C(board.SCL, board.SDA)
adcs = [ADS1115(i2c, address=addr) for addr in (0x48, 0x49, 0x4A, 0x4B)]
channels = [AnalogIn(adc, i) for adc in adcs for i in range(4)]
channels = channels[:SENSOR_COUNT]

# --- BLUETOOTH CONNECTION ---
client_sock = None

# Try using existing rfcomm0
if os.path.exists("/dev/rfcomm0"):
    try:
        client_sock = serial.Serial("/dev/rfcomm0", 9600)
        print("Using existing /dev/rfcomm0 connection")
    except serial.SerialException as e:
        print("Failed to open /dev/rfcomm0:", e)

# If not available, create server
if client_sock is None:
    server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
    server_sock.bind(("", bluetooth.PORT_ANY))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]
    print(f"No existing connection. Listening on RFCOMM port {port}...")
    client_sock, client_info = server_sock.accept()
    print(f"Connected to {client_info}")

# --- MAIN LOOP ---
try:
    while True:
        pressures = [min(max(ch.value / 32767, 0), 1) for ch in channels]
        line = ";".join(f"{p:.3f}" for p in pressures) + "\n"

        try:
            client_sock.write(line.encode()) if hasattr(client_sock, "write") else client_sock.send(line.encode())
        except Exception as e:
            print("Connection lost:", e)
            break

        time.sleep(READ_INTERVAL)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    if hasattr(client_sock, "close"):
        client_sock.close()
    if 'server_sock' in locals():
        server_sock.close()

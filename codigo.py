
#!/usr/bin/env python3
import time
import board
import busio
import serial
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import bluetooth

# --- CONFIG ---
PHONE_MAC = "7C:B0:73:73:FB:68"  # your phone MAC
SENSOR_COUNT = 13
READ_INTERVAL = 0.005  # 200 Hz

# --- I2C SETUP ---
i2c = busio.I2C(board.SCL, board.SDA)
adcs = [ADS1115(i2c, address=addr) for addr in (0x48, 0x49, 0x4A, 0x4B)]
channels = [AnalogIn(adc, i) for adc in adcs for i in range(4)]
channels = channels[:SENSOR_COUNT]

# --- BLUETOOTH SERVER SETUP ---
server_sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

# Try binding ports 1-30 until one works
RFCOMM_PORT = None
for port in range(1, 31):
    try:
        server_sock.bind(("", port))
        RFCOMM_PORT = port
        break
    except bluetooth.BluetoothError:
        continue

if RFCOMM_PORT is None:
    print("No free RFCOMM port found!")
    exit(1)

server_sock.listen(1)
print(f"Listening on RFCOMM port {RFCOMM_PORT}, waiting for phone...")

client_sock, client_info = server_sock.accept()
print(f"Connected to {client_info}")

# --- MAIN LOOP ---
try:
    while True:
        # Read and normalize sensors (0-1)
        pressures = [min(max(ch.value / 32767, 0), 1) for ch in channels]
        line = ";".join(f"{p:.3f}" for p in pressures) + "\n"

        try:
            client_sock.send(line.encode())
        except OSError as e:
            print("Connection lost:", e)
            break

        time.sleep(READ_INTERVAL)

except KeyboardInterrupt:
    print("Stopping...")

finally:
    client_sock.close()
    server_sock.close()

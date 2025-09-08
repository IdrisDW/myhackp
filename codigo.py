#!/usr/bin/env python3
import time
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
from bluedot.btcomm import BluetoothServer
from signal import pause

# --- CONFIG ---
SENSOR_COUNT = 13
READ_INTERVAL = 0.005  # 200 Hz

# --- I2C SETUP ---
i2c = busio.I2C(board.SCL, board.SDA)
adcs = [ADS1115(i2c, address=addr) for addr in (0x48, 0x49, 0x4A, 0x4B)]
channels = [AnalogIn(adc, i) for adc in adcs for i in range(4)]
channels = channels[:SENSOR_COUNT]

print(f"Channels initialized: {len(channels)}")

# --- MAIN LOOP ---
def data_received(data):
    print("Received from Android:", data)

    try:
        while True:
            pressures = [min(max(ch.value / 32767, 0), 1) for ch in channels]
            line = ";".join(f"{p:.3f}" for p in pressures) + "\n"
            server.send(line)
            print("Sent:", line.strip())
            time.sleep(READ_INTERVAL)
    except Exception as e:
        print("Connection lost:", e)

print("Bluetooth server listening...")
server = BluetoothServer(data_received)

pause()

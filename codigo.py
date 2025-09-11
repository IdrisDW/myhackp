#!/usr/bin/env python3
import time
import board
import busio
import signal
import sys
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
from bluedot.btcomm import BluetoothServer

# --- CONFIG ---
SENSOR_COUNT = 13
READ_INTERVAL = 0.005  # 200 Hz
WATCHDOG_TIMEOUT = 2.0  # seconds

# --- I2C SETUP ---
i2c = busio.I2C(board.SCL, board.SDA)
adcs = [ADS1115(i2c, address=addr) for addr in (0x48, 0x49, 0x4A, 0x4B)]
channels = [AnalogIn(adc, i) for adc in adcs for i in range(4)]
channels = channels[:SENSOR_COUNT]

print(f"Channels initialized: {len(channels)}")

# --- GLOBAL STATE ---
streaming = False
last_sent_time = time.time()

# --- Bluetooth handler ---
def data_received(data):
    global streaming
    print("Received from Android:", data)
    if data.strip().lower() == "start":
        streaming = True
    elif data.strip().lower() == "stop":
        streaming = False

# --- Graceful shutdown ---
def cleanup(signum, frame):
    print("\nStopping Bluetooth server...")
    server.stop()
    sys.exit(0)

signal.signal(signal.SIGINT, cleanup)
signal.signal(signal.SIGTERM, cleanup)

# --- Start Bluetooth server ---
print("Bluetooth server listening...")
server = BluetoothServer(data_received)

# --- Main loop with watchdog ---
try:
    while True:
        now = time.time()

        if streaming:
            try:
                pressures = [min(max(ch.value / 32767, 0), 1) for ch in channels]
                line = ";".join(f"{p:.3f}" for p in pressures) + "\n"
                server.send(line)
                print("Sent:", line.strip())
                last_sent_time = now
            except Exception as e:
                print("Connection lost:", e)
                streaming = False

        # Watchdog: check for silent failure
        if streaming and (now - last_sent_time > WATCHDOG_TIMEOUT):
            print("⚠️ Watchdog triggered: no data sent for >2s. Resetting stream.")
            streaming = False

        time.sleep(READ_INTERVAL)
except KeyboardInterrupt:
    cleanup(None, None)

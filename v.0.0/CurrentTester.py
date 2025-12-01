import serial
import time
import json
from statistics import mean
from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException

# ---------- CONFIG ----------
ARDUINO_PORT = 'COM3'
BAUD_RATE = 115200
CAL_FILE = 'phidget_calibration.json'
ANALOG_SERIAL = 678347

def setup_analog_channel(channel_number):
    ch = VoltageInput()
    ch.setDeviceSerialNumber(ANALOG_SERIAL)
    ch.setChannel(channel_number)
    ch.openWaitForAttachment(10000)
    ch.setDataInterval(8)
    return ch

def average_offset(channel):
    readings = []
    start = time.time()
    while time.time() - start < 10:
        try:
            readings.append(channel.getVoltage())
        except PhidgetException:
            continue
        time.sleep(0.01)
    return mean(readings)

print("Starting live current monitoring with Arduino control...")

try:
    with open(CAL_FILE, 'r') as f:
        cal_data = json.load(f)
        esc_slope = cal_data['esc_current_slope']
        esc_offset = cal_data['esc_current_offset']
        power_slope = cal_data['power_current_slope']
        power_offset = cal_data['power_current_offset']
except Exception as e:
    print(f"Error loading calibration file: {e}")
    exit(1)

try:
    ch_esc = setup_analog_channel(0)
    ch_power = setup_analog_channel(1)
except PhidgetException as e:
    print(f"Phidget setup error: {e.details}")
    exit(1)

print("Calibrating zero offsets...")
esc_zero_offset = average_offset(ch_esc)
power_zero_offset = average_offset(ch_power)

try:
    arduino = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
except serial.SerialException as e:
    print(f"Serial setup error: {e}")
    exit(1)

input("Press Enter to send 'S' and start the Arduino...")
arduino.write(b'S')

print("Now streaming current values. Press Ctrl+C to stop.\n")

try:
    while True:
        line = arduino.readline().decode('utf-8').strip()
        if line:
            print("ARDUINO:", line)

        try:
            esc_v = ch_esc.getVoltage()
            power_v = ch_power.getVoltage()

            esc_current = (esc_v - esc_zero_offset) * esc_slope + esc_offset
            power_current = (power_v - power_zero_offset) * power_slope + power_offset

            print(f"ESC_Current: {esc_current:.4f} A, Power_Current: {power_current:.4f} A")
            time.sleep(0.1)
        except PhidgetException:
            continue

except KeyboardInterrupt:
    print("\nMonitoring stopped.")
finally:
    ch_esc.close()
    ch_power.close()
    arduino.close()

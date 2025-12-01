import serial
import time
import csv
import threading
import json
import os
from statistics import mean
from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException

# ---------- CONFIG ----------
ARDUINO1_PORT = 'COM3'
ARDUINO2_PORT = 'COM7'
BAUD_RATE = 115200
LOG_FILE_BASE = 'combined_data_log'
CAL_FILE = 'phidget_calibration.json'

# ---------- PHIDGET SERIALS ----------
BRIDGE_SERIAL = 752185
ANALOG_SERIAL = 678347

# ---------- SHARED DATA ----------
bridge0_data = []
bridge1_data = []
analog0_data = []
analog1_data = []
analog2_data = []
optical_rpm_data = []

collecting_data = False
lock = threading.Lock()

# ---------- SENSOR THREAD ----------
def phidget_reader(bridge0, bridge1, analog0, analog1, analog2):
    global collecting_data
    while True:
        if collecting_data:
            try:
                v0 = bridge0.getVoltageRatio()
                v1 = bridge1.getVoltageRatio()
                a0 = analog0.getVoltage()
                a1 = analog1.getVoltage()
                a2 = analog2.getVoltage()

                with lock:
                    bridge0_data.append(v0)
                    bridge1_data.append(v1)
                    analog0_data.append(a0)
                    analog1_data.append(a1)
                    analog2_data.append(a2)
            except PhidgetException:
                pass
        time.sleep(0.008)

def optical_rpm_reader(arduino2_serial):
    global collecting_data
    while True:
        try:
            line = arduino2_serial.readline().decode('utf-8').strip()
            if line:
                rpm = float(line)
                if collecting_data and rpm > 0:
                    with lock:
                        optical_rpm_data.append(rpm)
        except Exception:
            pass

# ---------- SETUP ----------
def setup_bridge_channel(channel_number):
    ch = VoltageRatioInput()
    ch.setDeviceSerialNumber(BRIDGE_SERIAL)
    ch.setChannel(channel_number)
    ch.openWaitForAttachment(10000)
    ch.setDataInterval(8)
    return ch

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

def average_bridge_offset(channel):
    readings = []
    start = time.time()
    while time.time() - start < 10:
        try:
            readings.append(channel.getVoltageRatio())
        except PhidgetException:
            continue
        time.sleep(0.01)
    return mean(readings)

# Find unique CSV file name
log_index = 0
while True:
    log_filename = f"{LOG_FILE_BASE}_{log_index}.csv" if log_index else f"{LOG_FILE_BASE}.csv"
    if not os.path.exists(log_filename):
        break
    log_index += 1

print("Calibrating all offsets...")
try:
    bridge0 = setup_bridge_channel(0)
    bridge1 = setup_bridge_channel(1)
    analog0 = setup_analog_channel(0)
    analog1 = setup_analog_channel(1)
    analog2 = setup_analog_channel(2)
except PhidgetException as e:
    print(f"Phidget setup error: {e.details}")
    exit(1)

try:
    with open(CAL_FILE, 'r') as f:
        cal_data = json.load(f)
        torque_slope = cal_data['torque_slope']
        thrust_slope = cal_data['thrust_slope']
        esc_slope = cal_data['esc_current_slope']
        esc_offset = cal_data['esc_current_offset']
        power_slope = cal_data['power_current_slope']
        power_offset = cal_data['power_current_offset']
except Exception as e:
    print(f"Error loading calibration file: {e}")
    exit(1)

torque_offset = average_bridge_offset(bridge0)
thrust_offset = average_bridge_offset(bridge1)
esc_zero_offset = average_offset(analog0)
power_zero_offset = average_offset(analog1)

try:
    arduino1 = serial.Serial(ARDUINO1_PORT, BAUD_RATE, timeout=2)
    arduino2 = serial.Serial(ARDUINO2_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
except serial.SerialException as e:
    print(f"Serial setup error: {e}")
    exit(1)

input("Calibration complete. Type 'S' and press Enter to start logging: ")
arduino1.write(b'S')

threading.Thread(target=phidget_reader, args=(bridge0, bridge1, analog0, analog1, analog2), daemon=True).start()
threading.Thread(target=optical_rpm_reader, args=(arduino2,), daemon=True).start()

with open(log_filename, mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([
        'PWM', 'Mech_RPM', 'Opt_RPM', 'Air_Density',
        'Torque (Nm)', 'Thrust (N)',
        'ESC_Current', 'Power_Current', 'Power_Voltage'
    ])

    print("Logging started. Press Ctrl+C to stop.")

    try:
        while True:
            line = arduino1.readline().decode('utf-8').strip()
            if not line:
                continue

            if line.startswith("PWM:"):
                print(line)
                collecting_data = False
                time.sleep(3)
                with lock:
                    bridge0_data.clear()
                    bridge1_data.clear()
                    analog0_data.clear()
                    analog1_data.clear()
                    analog2_data.clear()
                    optical_rpm_data.clear()
                collecting_data = True
                continue

            arduino_values = line.split(',')
            if len(arduino_values) < 3:
                continue

            with lock:
                avg0 = mean(bridge0_data) if bridge0_data else 0.0
                avg1 = mean(bridge1_data) if bridge1_data else 0.0
                esc_voltage = mean(analog0_data) if analog0_data else 0.0
                power_voltage_raw = mean(analog1_data) if analog1_data else 0.0
                v_div = mean(analog2_data) if analog2_data else 0.0
                optical_avg = mean(optical_rpm_data) if optical_rpm_data else 0.0

                esc_current = (esc_voltage - esc_zero_offset) * esc_slope + esc_offset
                power_current = (power_voltage_raw - power_zero_offset) * power_slope + power_offset
                power_voltage = v_div * 5

                torque = (avg0 - torque_offset) * torque_slope
                thrust = (avg1 - thrust_offset) * thrust_slope

                collecting_data = False
                bridge0_data.clear()
                bridge1_data.clear()
                analog0_data.clear()
                analog1_data.clear()
                analog2_data.clear()
                optical_rpm_data.clear()

            row = arduino_values[:2] + [optical_avg, arduino_values[2], torque, thrust, esc_current, power_current, power_voltage]
            writer.writerow(row)
            print(row)

    except KeyboardInterrupt:
        print("Logging stopped.")
    finally:
        bridge0.close()
        bridge1.close()
        analog0.close()
        analog1.close()
        analog2.close()
        arduino1.close()
        arduino2.close()

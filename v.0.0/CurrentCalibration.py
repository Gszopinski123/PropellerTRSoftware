import serial
import time
import json
from statistics import mean
from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException

ARDUINO1_PORT = 'COM3'
BAUD_RATE = 115200
CAL_FILE = 'phidget_calibration.json'

ESC_CHANNEL = 0
POWER_CHANNEL = 1

def setup_channel(channel_number):
    ch = VoltageInput()
    ch.setChannel(channel_number)
    ch.openWaitForAttachment(10000)
    ch.setDataInterval(8)
    return ch

def average_offset(ch):
    readings = []
    print(f"Calibrating offset for channel {ch.getChannel()}...")
    start = time.time()
    while time.time() - start < 10:
        try:
            readings.append(ch.getVoltage())
        except PhidgetException:
            continue
        time.sleep(0.01)
    return mean(readings)

def collect_calibration_data(arduino, ch_esc, ch_power, offset_esc, offset_power):
    esc_data = []
    power_data = []
    print("Type in the measured current in Amps during each 15s motor run. Type 'done' to finish and compute calibration.")

    try:
        while True:
            line = arduino.readline().decode('utf-8').strip()
            if not line:
                continue

            if line.startswith("PWM:"):
                print(line)
                time.sleep(3)

                esc_voltages = []
                power_voltages = []
                start = time.time()
                while time.time() - start < 10:
                    try:
                        esc_v = ch_esc.getVoltage() - offset_esc
                        power_v = ch_power.getVoltage() - offset_power
                        esc_voltages.append(esc_v)
                        power_voltages.append(power_v)
                    except PhidgetException:
                        continue
                    time.sleep(0.01)

                try:
                    user_input = input("Measured current (Amps) or 'done': ").strip()
                    if user_input.lower() == 'done':
                        break
                    true_current = float(user_input)

                    esc_data.append((mean(esc_voltages), true_current))
                    power_data.append((mean(power_voltages), true_current))
                except ValueError:
                    print("Invalid current input. Skipping this measurement.")
    except KeyboardInterrupt:
        print("\nCalibration interrupted. Saving data collected so far...")

    return esc_data, power_data

def calculate_slope_and_offset(data):
    if not data:
        return 0.0, 0.0
    x = [v for v, _ in data]
    y = [i for _, i in data]
    n = len(x)
    mean_x = mean(x)
    mean_y = mean(y)
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0.0
    offset = mean_y - slope * mean_x
    return slope, offset

print("Starting current sensor calibration...")

ch_esc = setup_channel(ESC_CHANNEL)
ch_power = setup_channel(POWER_CHANNEL)

print("Calibrating zero offsets...")
offset_esc = average_offset(ch_esc)
offset_power = average_offset(ch_power)

try:
    arduino = serial.Serial(ARDUINO1_PORT, BAUD_RATE, timeout=2)
    time.sleep(2)
except serial.SerialException as e:
    print(f"Serial setup error: {e}")
    exit(1)

input("Press Enter to send 'S' and start the Arduino...")
arduino.write(b'S')

esc_data, power_data = collect_calibration_data(arduino, ch_esc, ch_power, offset_esc, offset_power)

esc_slope, esc_intercept = calculate_slope_and_offset(esc_data)
power_slope, power_intercept = calculate_slope_and_offset(power_data)

print(f"ESC slope: {esc_slope:.6f}, offset: {esc_intercept:.6f}")
print(f"Power slope: {power_slope:.6f}, offset: {power_intercept:.6f}")

# Save to JSON
try:
    with open(CAL_FILE, 'r') as f:
        cal_data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    cal_data = {}

cal_data['esc_current_slope'] = esc_slope
cal_data['esc_current_offset'] = esc_intercept
cal_data['power_current_slope'] = power_slope
cal_data['power_current_offset'] = power_intercept

with open(CAL_FILE, 'w') as f:
    json.dump(cal_data, f, indent=4)

print("Calibration saved.")

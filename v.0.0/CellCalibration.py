import json
import time
from statistics import mean
from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException

BRIDGE_SERIAL = 752185
CAL_FILE = 'phidget_calibration.json'
G = 9.80665  # m/s^2


def setup_channel(ch_num):
    ch = VoltageRatioInput()
    ch.setDeviceSerialNumber(BRIDGE_SERIAL)
    ch.setChannel(ch_num)
    ch.openWaitForAttachment(10000)
    ch.setDataInterval(8)
    return ch


def average_offset(ch):
    readings = []
    print("Calibrating zero offset... Make sure no load is applied.")
    start = time.time()
    while time.time() - start < 10:
        try:
            readings.append(ch.getVoltageRatio())
        except PhidgetException:
            continue
        time.sleep(0.01)
    return mean(readings)


def collect_calibration_data(ch, offset, is_torque, arm_mm=None):
    measurements = []
    print("Type mass in grams to start a sample or 'done' to finish.")

    while True:
        entry = input("Enter mass (g) or 'done': ").strip()
        if entry.lower() == 'done':
            break
        try:
            mass_g = float(entry)
            force_N = (mass_g / 1000.0) * G
            if is_torque:
                if arm_mm is None:
                    raise ValueError("Arm length is required for torque mode.")
                torque = (arm_mm / 1000.0) * force_N
                target = torque
            else:
                target = force_N
        except ValueError:
            print("Invalid input. Try again.")
            continue

        print("Collecting data for 10 seconds...")
        readings = []
        time.sleep(1)
        start = time.time()
        while time.time() - start < 10:
            try:
                v = ch.getVoltageRatio() - offset
                readings.append(v)
            except PhidgetException:
                continue
            time.sleep(0.01)

        avg = mean(readings)
        measurements.append((avg, target))
        print(f"Recorded: {avg:.6f} -> {target:.4f}\n")

    return measurements


def calculate_slope(data):
    x = [v for v, _ in data]
    y = [f for _, f in data]
    n = len(x)
    mean_x = mean(x)
    mean_y = mean(y)
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    return numerator / denominator if denominator != 0 else 0.0


def calibrate():
    ch_input = input("Which input are you calibrating? (0=Torque, 1=Thrust): ").strip()
    if ch_input not in ['0', '1']:
        print("Invalid input number.")
        return

    ch_num = int(ch_input)
    ch = setup_channel(ch_num)
    is_torque = ch_num == 0

    arm_mm = None
    if is_torque:
        try:
            arm_mm = float(input("Enter torque arm length in mm: ").strip())
        except ValueError:
            print("Invalid arm length.")
            return

    offset = average_offset(ch)
    print(f"Zero offset: {offset:.8f}\n")

    data = collect_calibration_data(ch, offset, is_torque, arm_mm)
    slope = calculate_slope(data)

    print(f"Calculated slope: {slope:.6f}")

    # Save to JSON
    try:
        with open(CAL_FILE, 'r') as f:
            cal_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        cal_data = {}

    if is_torque:
        cal_data['torque_slope'] = slope
        cal_data['torque_offset'] = offset
    else:
        cal_data['thrust_slope'] = slope
        cal_data['thrust_offset'] = offset

    with open(CAL_FILE, 'w') as f:
        json.dump(cal_data, f, indent=4)
    print("Calibration saved.")


if __name__ == '__main__':
    calibrate()

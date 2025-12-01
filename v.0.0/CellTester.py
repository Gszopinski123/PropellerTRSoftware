import time
import json
from statistics import mean
from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException

BRIDGE_SERIAL = 752185
CAL_FILE = 'phidget_calibration.json'
G = 9.80665

UNIT_CHOICES = {
    'SI': ('Nm', 'N'),
    'I': ('in-oz', 'lbs')
}

TORQUE_CONVERSION = 141.6129  # Nm to in-oz
FORCE_CONVERSION = 0.224809   # N to lbs

def setup_channel(ch_num):
    ch = VoltageRatioInput()
    ch.setDeviceSerialNumber(BRIDGE_SERIAL)
    ch.setChannel(ch_num)
    ch.openWaitForAttachment(10000)
    ch.setDataInterval(8)
    return ch

def average_offset(ch):
    readings = []
    print("Calibrating offset... do not apply load.")
    start = time.time()
    while time.time() - start < 10:
        try:
            readings.append(ch.getVoltageRatio())
        except PhidgetException:
            continue
        time.sleep(0.01)
    return mean(readings)

def read_loop(ch0, ch1, slope0, slope1, offset0, offset1, unit_mode):
    torque_unit, force_unit = UNIT_CHOICES[unit_mode]
    while True:
        try:
            val0 = ch0.getVoltageRatio() - offset0 if ch0 else None
            val1 = ch1.getVoltageRatio() - offset1 if ch1 else None

            torque = val0 * slope0 if val0 is not None else None
            thrust = val1 * slope1 if val1 is not None else None

            if unit_mode == 'I':
                if torque is not None:
                    torque *= TORQUE_CONVERSION
                if thrust is not None:
                    thrust *= FORCE_CONVERSION

            output = []
            if torque is not None:
                output.append(f"Torque: {torque:.4f} {torque_unit}")
            if thrust is not None:
                output.append(f"Thrust: {thrust:.4f} {force_unit}")
            print(" | ".join(output))

        except PhidgetException:
            pass

        time.sleep(0.2)

def tester():
    try:
        with open(CAL_FILE, 'r') as f:
            data = json.load(f)
            slope0 = data.get('torque_slope')
            slope1 = data.get('thrust_slope')
            offset0 = data.get('torque_offset')
            offset1 = data.get('thrust_offset')
    except (FileNotFoundError, json.JSONDecodeError):
        print("Calibration file not found or invalid.")
        return

    mode = input("Which input(s) to test? (0, 1, both): ").strip()
    if mode not in ["0", "1", "both"]:
        print("Invalid mode.")
        return

    unit_mode = input("Output units? (SI/I): ").strip().upper()
    if unit_mode not in UNIT_CHOICES:
        print("Invalid unit mode.")
        return

    ch0 = ch1 = None
    live_offset0 = live_offset1 = 0.0

    if mode == '0' or mode == 'both':
        ch0 = setup_channel(0)
        live_offset0 = average_offset(ch0)
    if mode == '1' or mode == 'both':
        ch1 = setup_channel(1)
        live_offset1 = average_offset(ch1)

    print("--- Live Data ---")
    read_loop(ch0, ch1, slope0, slope1, live_offset0 if ch0 else 0, live_offset1 if ch1 else 0, unit_mode)

if __name__ == '__main__':
    tester()

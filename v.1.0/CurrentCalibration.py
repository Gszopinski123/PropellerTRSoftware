import serial
import time
from prop_lib import (calculate_slope,CALIBRATION_CONFIG,jsonFillFile,openAsReadJson)
from phidgetInterface import AnalogInterface

def collect_calibration_data(arduino, ch_esc, ch_power,lsOfAmps):
    esc_data = []
    power_data = []
    print("Type in the measured current in Amps during each 15s motor run. Type 'done' to finish and compute calibration.")
    # test this
    try:
        for x in lsOfAmps:
            line = arduino.readline().decode('utf-8').strip()
            if not line:
                continue

            if line.startswith("PWM:"):
                print(line)
                time.sleep(3)

                esc_voltages = ch_esc.calculateAverageVoltage()
                power_voltages = ch_power.calculateAverageVoltage()
                # TURN INTO LIST OF MEASURE AMPS
                user_input = x
                esc_data.append((esc_voltages, user_input))
                power_data.append((power_voltages, user_input))
    except KeyboardInterrupt: #maybe enter q instead
        print("\nCalibration interrupted. Saving data collected so far...")

    return esc_data, power_data
def calibrate(ls):
    options = ["esc","power"]
    print("Starting current sensor calibration...")
    print("Calibrating zero offsets...")
    json_cfg = openAsReadJson("cfg.json")
    if "ESC_CHANNEL" not in json_cfg:
        print("No ESC_CHANNEL in config")
        exit()
    if "POWER_CHANNEL" not in json_cfg:
        print("No POWER_CHANNEL in config")
        exit()
    if "BAUD_RATE" not in json_cfg:
        print("No BAUD_RATE in config!")
        exit()
    if "ARDUINO1_PORT" not in json_cfg:
        print("No ARDUINO1_PORT in config")
        exit()
    if "ANALOG_SERIAL" not in json_cfg:
        print("No ANALOG_SERIAL in config!")
        exit(1)
    esc_channel = json_cfg["ESC_CHANNEL"]
    power_channel = json_cfg["POWER_CHANNEL"]
    analog_serial = json_cfg["ANALOG_SERIAL"]
    # offset_esc, esc, option_esc = calibrate_setup("ANALOG_SERIAL",esc_channel,options)
    # offset_power, power, option_power = calibrate_setup("ANALOG_SERIAL",power_channel,options)
    
    arduino = serial.Serial(json_cfg["ARDUINO1_PORT"], json_cfg["BAUD_RATE"], timeout=2)
    
    time.sleep(2)

    #input("Press Enter to send 'S' and start the Arduino...")
    arduino.write(b'S')
    esc = AnalogInterface(analog_serial,esc_channel)
    power = AnalogInterface(analog_serial,power_channel)
    esc_data, power_data = collect_calibration_data(arduino, esc, power,ls)

    esc_slope, esc_intercept = calculate_slope(esc_data)
    power_slope, power_intercept = calculate_slope(power_data)

    print(f"ESC slope: {esc_slope:.6f}, offset: {esc_intercept:.6f}")
    print(f"Power slope: {power_slope:.6f}, offset: {power_intercept:.6f}")
    
    cal_data = {}
    cal_data['esc_current_slope'] = esc_slope
    cal_data['esc_current_offset'] = esc_intercept
    cal_data['power_current_slope'] = power_slope
    cal_data['power_current_offset'] = power_intercept
    jsonFillFile(CALIBRATION_CONFIG,cal_data)

    print("Calibration saved.")

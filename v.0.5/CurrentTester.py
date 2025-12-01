import serial
import time
from prop_lib import CALIBRATION_CONFIG, openAsReadJson
from phidgetInterface import AnalogInterface

def main():
    setup()


def setup():
    print("Starting live current monitoring with Arduino control...")
    json_cal_config = openAsReadJson(CALIBRATION_CONFIG)
    if 'esc_current_slope' in json_cal_config:
        esc_slope = json_cal_config['esc_current_slope']
    if 'esc_current_offset' in json_cal_config:
        esc_offset = json_cal_config['esc_current_offset']
    if 'power_current_slope' in json_cal_config:
        power_slope = json_cal_config['power_current_slope']
    if 'power_current_offset' in json_cal_config:
        power_offset = json_cal_config['power_current_offset']
    json_cfg = openAsReadJson("cfg.json")
    analog_serial = json_cfg["ANALOG_SERIAL"]
    esc = AnalogInterface(analog_serial,json_cfg["ESC_CHANNEL"])
    power = AnalogInterface(analog_serial,json_cfg["POWER_CHANNEL"])

    print("Calibrating zero offsets...")
    


    arduino = serial.Serial(json_cfg["ARDUINO_PORT"], json_cfg["BAUD_RATE"], timeout=2)
    time.sleep(2)

    input("Press Enter to send 'S' and start the Arduino...")
    arduino.write(b'S')
    print("Now streaming current values. Press Ctrl+C to stop.\n")
    tester(arduino,esc,power,esc_slope,esc_offset,power_slope,power_offset)

    
def tester(arduino,esc,power,esc_slope,esc_offset,power_slope,power_offset):
    esc_zero_offset = esc.calculateAverageVoltage()
    power_zero_offset = power.calculateAverageVoltage()
    try:
        while True:
            line = arduino.readline().decode('utf-8').strip()
            if line:
                print("ARDUINO:", line)

            
            esc_v = esc.voltageReadIn()
            power_v = power.voltageReadIn()

            esc_current = (esc_v - esc_zero_offset) * esc_slope + esc_offset
            power_current = (power_v - power_zero_offset) * power_slope + power_offset

            print(f"ESC_Current: {esc_current:.4f} A, Power_Current: {power_current:.4f} A")
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
    finally:
        esc.close()
        power.close()
        arduino.close()


if __name__ == "__main__":
    main()
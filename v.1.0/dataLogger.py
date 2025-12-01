import serial
import time
import csv
import threading
import json
import os
from prop_lib import openAsReadJson, BridgeInterface, AnalogInterface
from statistics import mean
from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException

lock = threading.Lock()
optical_rpm_data = []
collecting_data = False

def main(prop="",lr=""):
    #GET CONFIGURATION
    cfgFile = openAsReadJson("cfg.json")
    ARDUINO1_PORT = cfgFile['ARDUINO1_PORT']
    ARDUINO2_PORT = cfgFile['ARDUINO2_PORT']
    BAUD_RATE = cfgFile['BAUD_RATE']
    LOG_FILE_BASE = 'combined_data_log'
    CAL_FILE = cfgFile["CELL_CAL_FILE"]
    BRIDGE_SERIAL = cfgFile['BRIDGE_SERIAL']
    ANALOG_SERIAL = cfgFile['ANALOG_SERIAL']
    # SETUP CHANNELS
    channels = []
    data_for_channels = []
    torque_channel = BridgeInterface(BRIDGE_SERIAL,0)
    thrust_channel = BridgeInterface(BRIDGE_SERIAL,1)
    analog0 = AnalogInterface(ANALOG_SERIAL,0)
    analog1 = AnalogInterface(ANALOG_SERIAL,1)
    analog2 = AnalogInterface(ANALOG_SERIAL,2)
    channels.append(torque_channel)
    data_for_channels.append([])
    channels.append(thrust_channel)
    data_for_channels.append([])
    channels.append(analog0)
    data_for_channels.append([])
    channels.append(analog1)
    data_for_channels.append([])
    channels.append(analog2)
    data_for_channels.append([])
    

    
    
    cal_data = openAsReadJson(CAL_FILE)

    torque_slope = cal_data['torque_slope']
    thrust_slope = cal_data['thrust_slope']
    esc_slope = cal_data['esc_current_slope']
    esc_offset = cal_data['esc_current_offset']
    power_slope = cal_data['power_current_slope']
    power_offset = cal_data['power_current_offset']
    torque_offset = torque_channel.calculateAverageVoltage()
    thrust_offset = thrust_channel.calculateAverageVoltage()
    esc_zero_offset = analog0.calculateAverageVoltage()
    power_zero_offset = analog1.calculateAverageVoltage()


    arduino1 = serial.Serial(ARDUINO1_PORT, BAUD_RATE, timeout=2)
    arduino2 = serial.Serial(ARDUINO2_PORT, BAUD_RATE, timeout=1)
    time.sleep(2)
    # input("Calibration complete. Type 'S' and press Enter to start logging: ")
    arduino1.write(b'S')

    threading.Thread(target=phidget_reader, args=(channels,data_for_channels), daemon=True).start()
    threading.Thread(target=optical_rpm_reader, args=(arduino2,), daemon=True).start()
    propeller_name = prop
    right_or_left = lr
    log_filename = propeller_name+"_"+right_or_left
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
                        for i in data_for_channels:
                            i.clear()
                        optical_rpm_data.clear()
                    collecting_data = True
                    continue

                arduino_values = line.split(',')
                if len(arduino_values) < 3:
                    continue

                with lock:
                    averages = []
                    for i in data_for_channels:
                        averages.append(mean(i) if i else 0.0)
                    
                    optical_avg = mean(optical_rpm_data) if optical_rpm_data else 0.0

                    esc_current = (averages[2] - esc_zero_offset) * esc_slope + esc_offset
                    power_current = (averages[3] - power_zero_offset) * power_slope + power_offset
                    power_voltage = averages[4] * 5

                    torque = (averages[0] - torque_offset) * torque_slope
                    thrust = (averages[1] - thrust_offset) * thrust_slope

                    collecting_data = False
                    for i in data_for_channels:
                        i.clear()
                    optical_rpm_data.clear()

                row = arduino_values[:2] + [optical_avg, arduino_values[2], torque, thrust, esc_current, power_current, power_voltage]
                writer.writerow(row)
                print(row)
            

        except KeyboardInterrupt:
            print("Logging stopped.")
        finally:
            for i in channels:
                i.close()
            arduino1.close()
            arduino2.close()


# ---------- SENSOR THREAD ----------
def phidget_reader(channels,data_for_channels):
    global collecting_data
    while True:
        if collecting_data:
            for i in range(len(channels)):
                with lock:
                    data_for_channels.append(channels[i].voltageReadIn())
        time.sleep(0.008)

def optical_rpm_reader(arduino2_serial):
    global collecting_data
    while True:
        line = arduino2_serial.readline().decode('utf-8').strip()
        if line:
            rpm = float(line)
            if collecting_data and rpm > 0:
                with lock:
                    optical_rpm_data.append(rpm)


if __name__ == "__main__":
    main()
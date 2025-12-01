from phidgetInterface import BridgeInterface
from prop_lib import (parseInput, force_newtons, newton_meters, 
                      jsonFillFile, calculate_slope,CALIBRATION_CONFIG,calibrate_setup)


def main():
    final_cal_data = {}
    channel = choose_channel()
    offset, bridge, torqueorthrust = calibrate_setup("BRIDGE_SERIAL",channel,["torque","thrust"])
    measurementdata = calibrate(offset,channel,bridge)
    slope,_ = calculate_slope(measurementdata)
    final_cal_data[f"{torqueorthrust}_slope"] = slope
    jsonFillFile(CALIBRATION_CONFIG,final_cal_data)


def choose_channel():
    channels_for_cell = [1,2]
    valid, channel = parseInput(channels_for_cell,"Which input are you calibrating? (0=Torque, 1=Thrust): ")
    if not valid:
        exit(1)
    return int(channel)


def calibrate(channel_number : int, offset : float, bridge : BridgeInterface) -> list[tuple[float,float]]:
    measurements = []
    loop_valid = True
    valid_torque = False
    if channel_number == 0:
        valid_torque,arm_mm = parseInput([],"Enter torque arm length in mm: ")

    while loop_valid:
        loop_valid, mass_g = parseInput([],"Enter mass (g): ")
        
        if not loop_valid:
            continue
        force_n = force_newtons(mass_g)
        target = force_n
        
        if valid_torque:
            target = newton_meters(arm_mm,target)
        
        avg = bridge.calculateAverageVoltageRatio(offset)
        measurements.append((avg, target))

    return measurements

if __name__ == "__main__":
    main()
from phidgetInterface import BridgeInterface
from prop_lib import (parseInput, force_newtons, newton_meters, 
                      jsonFillFile, calculate_slope,CALIBRATION_CONFIG,calibrate_setup)



def setup(channel,arm_mm,listOfWeights):
    final_cal_data = {}
    offset, bridge, torqueorthrust = calibrate_setup("BRIDGE_SERIAL",channel,["torque","thrust"])
    measurementdata = calibrate(offset,channel,bridge,arm_mm,listOfWeights)
    slope,_ = calculate_slope(measurementdata)
    final_cal_data[f"{torqueorthrust}_slope"] = slope
    jsonFillFile(CALIBRATION_CONFIG,final_cal_data)

def choose_channel():
    channels_for_cell = [1,2]
    valid, channel = parseInput(channels_for_cell,"Which input are you calibrating? (0=Torque, 1=Thrust): ")
    if not valid:
        exit(1)
    return channel


def calibrate(channel_number : int, offset : float, bridge : BridgeInterface,arm_mm,listOfWeights) -> list[tuple[float,float]]:
    measurements = []
    valid_torque = True if channel_number == 0 else False

    for x in listOfWeights:
        force_n = force_newtons(x)
        target = force_n
        
        if valid_torque:
            target = newton_meters(arm_mm,target)
        
        avg = bridge.calculateAverageVoltageRatio(offset)
        measurements.append((avg, target))

    return measurements

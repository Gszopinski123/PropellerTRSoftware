import json
import os
from statistics import mean
from phidgetInterface import AnalogInterface, BridgeInterface

GRAVITY_CONSTANT = 9.80665
TORQUE_CONVERSION = 141.6129
FORCE_CONVERSION = 0.224809 
CALIBRATION_CONFIG="phidget_calibration.json"
UNIT_CHOICES = {
    'SI': ('Nm', 'N'),
    'I': ('in-oz', 'lbs')}


def force_newtons(mass_g : float) -> float:
    mass_kilograms = (mass_g / 1000.0)
    return mass_kilograms * GRAVITY_CONSTANT

def newton_meters(measurement_mm: float, force_n: float) -> float:
    measurement_meters = (measurement_mm / 1000.0)
    return measurement_meters * force_n 

def parseInput(condition : list[int], msg : str) -> tuple[bool, any]:
    parsed = input(f"{msg}")
    if parsed.isdigit() and int(parsed) in condition:
        return True, int(parsed)
    elif parsed.isdigit():
        return True, float(parsed)
    elif parsed in condition:
        return True, parsed
    else:
        return False, -1

        
def openAsReadJson(filename : str):
    with open(filename,"r") as file:
        json_file = json.load(file)
    return json_file

def jsonFillFile(filename : str, calibration_data: dict[str, float]) -> None:
    json_file = {}
    if os.path.exists(filename):
        with open(filename,'r') as file:
            json_file = json.load(file)
            print(json_file)
            json_file.update(calibration_data)
    with open(filename,'w') as file:
        json_file.update(calibration_data)
        json.dump(json_file,file,indent=4)


def calculate_slope(data : list[tuple[float, float]]) -> tuple[float, float]:
    x = []
    y = []
    for n,m in data:
        x+=[n]; y+=[m];
    n = len(x)
    mean_x = mean(x)
    mean_y = mean(y)
    numerator = sum((x[i] - mean_x) * (y[i] - mean_y) for i in range(n))
    denominator = sum((x[i] - mean_x) ** 2 for i in range(n))
    slope = numerator / denominator if denominator != 0 else 0.0
    offset = mean_y - slope * mean_x
    return slope, offset

def calibrate_setup(serial_type,channel=-1,options=[]) -> tuple[float,int,BridgeInterface,str]:
    cfg_json = openAsReadJson("cfg.json")
    bridge_analog_serial = cfg_json[serial_type]
    bridge = None
    if serial_type == "BRIDGE_SERIAL":
        bridge = BridgeInterface(bridge_analog_serial,channel)
    else:
        bridge = AnalogInterface(bridge_analog_serial,channel)
    print("Running offset!")
    offset = bridge.calculateAverageVoltage()
    return offset, bridge, options[channel]
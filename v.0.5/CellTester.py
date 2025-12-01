from prop_lib import CALIBRATION_CONFIG, openAsReadJson, parseInput,UNIT_CHOICES,TORQUE_CONVERSION,FORCE_CONVERSION
from phidgetInterface import BridgeInterface
import time

def main():
   tester()

def checkModesAvailable():
    json_cal_cfg = openAsReadJson(CALIBRATION_CONFIG)
    slope_flag = 0
    slopes = []

    if "torque_slope" in json_cal_cfg:
        slopes += [json_cal_cfg["torque_slope"]]
        slope_flag += 1
    if "thrust_slope" in json_cal_cfg:
        slopes += [json_cal_cfg["thrust_slope"]]
        slope_flag += 2
    
    modes_available = []
    
    if (slope_flag & 3) == 3:
        modes_available = [0,1,2]
    elif (slope_flag & 1) == 1:
        modes_available = [0]
    elif (slope_flag & 2) == 2:
        modes_available = [1]
    if modes_available == []:
        print("Please Calibrate No Available Modes!")
        return 
    
    return modes_available, slopes

def setupBridge(modes_available):
    json_file = openAsReadJson("cfg.json")
    if "SERIAL_NUMBER" not in json_file:
        print("Cfg is incomplete! SERIAL_NUMBER MISSING!")
        exit()
    serial_number = json_file["SERIAL_NUMBER"]
    print("Modes: 0: torque, 1: thrust, 2: both")
    valid, mode = parseInput(modes_available,f"Modes Available: {modes_available}")
    if not valid:
        print("Invalid Mode!")
        exit()
    valid, unit_mode = parseInput(UNIT_CHOICES,"Output units? (SI/I): ")
    if not valid:
        print("Invalid Unit Mode!")
        exit()
    thrust_bridge = None
    torque_bridge = None
    if mode == 1 or mode == 2:
        thrust_bridge = BridgeInterface(serial_number,1)
    if mode == 0 or mode == 2:
        torque_bridge = BridgeInterface(serial_number,0)
    return thrust_bridge, torque_bridge, unit_mode

def tester():
    modes_available, slopes = checkModesAvailable()
    thrust, torque, unit_mode = setupBridge(modes_available)
    torque_offset = -1
    thrust_offset = -1
    if thrust:
        thrust_offset = thrust.calculateAverageVoltage()
    if torque:
        torque_offset = torque.calculateAverageVoltage()
    read_loop(torque,thrust,slopes[0],slopes[1],torque_offset,thrust_offset,unit_mode)
    
def read_loop(torque, thrust, torque_slope, thrust_slope, torque_offset, thrust_offset, unit_mode,loop=-1):
    torque_unit, force_unit = UNIT_CHOICES[unit_mode]
    while (loop != 0):
        if torque:
            result_torque = torque.calculateAverageVoltage(torque_offset)
            result_torque = result_torque * torque_slope
            if unit_mode == 'I':
                result_torque *= TORQUE_CONVERSION
            print(f"Torque: {result_torque:.4f} {torque_unit} | ",end="")
        if thrust:
            result_thrust = thrust.calculateAverageVoltage(thrust_offset)
            result_thrust = result_thrust * thrust_slope
            if unit_mode == 'I':
                result_thrust *= FORCE_CONVERSION
            print(f"Thrust: {result_thrust:.4f} {force_unit}")
        time.sleep(0.2)
        loop += 1



if __name__ == "__main__":
    main()
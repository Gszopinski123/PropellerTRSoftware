from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.PhidgetException import PhidgetException
import time

try:
    bridge = VoltageRatioInput()
    bridge.setDeviceSerialNumber(752185)
    bridge.setChannel(1)
    bridge.openWaitForAttachment(10000)
    bridge.setDataInterval(8)

    print("PhidgetBridge connected. Reading values:")
    while True:
        val = bridge.getVoltageRatio()
        print(f"Voltage Ratio: {val}")
        time.sleep(0.1)

except PhidgetException as e:
    print(f"Error: {e.details}")
finally:
    try:
        bridge.close()
    except:
        pass

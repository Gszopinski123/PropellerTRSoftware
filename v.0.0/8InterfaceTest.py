from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException
import time

try:
    analog = VoltageInput()
    analog.setDeviceSerialNumber(678347)
    analog.setChannel(0)
    analog.openWaitForAttachment(10000)
    analog.setDataInterval(8)

    print("8/8/8 Analog input connected. Reading voltages:")
    while True:
        voltage = analog.getVoltage()
        print(f"Voltage: {voltage:.4f} V")
        time.sleep(0.1)

except PhidgetException as e:
    print(f"Error: {e.details}")
finally:
    try:
        analog.close()
    except:
        pass

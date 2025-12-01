from Phidget22.Devices.VoltageRatioInput import VoltageRatioInput
from Phidget22.Devices.VoltageInput import VoltageInput
from Phidget22.PhidgetException import PhidgetException
from statistics import mean
import time


class PhidgetInterface:
    def __init__(self, serialNumber: int, channelNumber: int, instantiated=True) -> int:
        self.offset = 0
        # Timing
        waitForConnectionTime = 10000
        dataUpdateInterval = 8
        # Safety Check
        if (not self.device):
            print("Not recognized device type!")
            return -1
        if (instantiated):
            raise Exception("Phidget Interface should not be instantiated!")
        # Intializing device
        print("Setting Serial Number: ",serialNumber)
        self.device.setDeviceSerialNumber(serialNumber)
        print("Serial number set!")
        print("Setting channel number: ",channelNumber)
        self.device.setChannel(channelNumber)
        print("Channel number set!")
        print("Waiting for connection!")
        self.device.openWaitForAttachment(waitForConnectionTime)
        print("Connection Success!")
        print("Setting data interval!")
        self.device.setDataInterval(dataUpdateInterval)
        print("Data interval set!")
        return 0

    def run(self,loopCount=-1) -> None:
        i = 0
        while i < loopCount:
            i += 1
            print(f"{self.typeVoltageRead}: {self.voltageReadIn():.4f}")
            time.sleep(0.1)

    
    def calculateAverageVoltage(self,offset=0) -> float:
        readings = []
        time.sleep(1)
        start = time.time()
        while time.time() - start < 10:
            readings.append(self.voltageReadIn()-offset)
            time.sleep(0.01)
        return mean(readings)
    
    def set_offset(self) -> None:
        self.offset = self.calculateAverageVoltage()
    
    def get_offset(self) -> float:
        return self.offset
    
    def reset_offset(self) -> None:
        self.offset = 0

    def close(self) -> int:
        self.device.close()
        return 0

class AnalogInterface(PhidgetInterface):
    def __init__(self, serialNumber: int, channelNumber: int) -> int:
        self.device = VoltageInput()
        self.typeVoltageRead = "Voltage"
        self.voltageReadIn = lambda: self.device.getVoltage()
        isInstantiated = False
        super().__init__(serialNumber,channelNumber,isInstantiated)
    def calculateAverageVoltage(self, offset=0):
        return super().calculateAverageVoltage(offset)


class BridgeInterface(PhidgetInterface):
    def __init__(self, serialNumber: int, channelNumber: int) -> int:
        self.device = VoltageRatioInput()
        self.typeVoltageRead = "VoltageRatio"
        self.voltageReadIn = lambda: self.device.getVoltageRatio()
        isInstantiated = False
        super().__init__(serialNumber,channelNumber,isInstantiated)
    def calculateAverageVoltageRatio(self, offset=0) -> int:
        return super().calculateAverageVoltage(offset)
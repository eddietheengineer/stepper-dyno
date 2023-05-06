import time
import numpy as np
from riden import Riden
from dataclasses import dataclass

riden = Riden(port="/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
              baudrate=115200, address=1)


@dataclass
class powersupplydata:
    measuredvoltage: float = 0
    measuredpower: float = 0
    samplecount: int = 0
    capturetime: float = 0


def measure(sampleCount):
    start = time.perf_counter()
    measurements_power = []
    for _ in range(sampleCount):
        val = riden.get_p_out()
        measurements_power.append(val)
        time.sleep(0.1)
    filtered_data = reject_range_outliers(np.array(measurements_power))
    output = powersupplydata()
    output.measuredpower = round(np.average(filtered_data), 2)
    output.capturetime = round(time.perf_counter() - start, 2)
    output.samplecount = len(filtered_data)
    output.measuredvoltage = riden.get_v_out()
    return output


def reject_range_outliers(data, allowedrange=0.2):
    d = np.abs(data - np.median(data))
    return data[d < allowedrange]


def voltage_setting(voltage):
    riden.set_v_set(voltage)
    riden.set_output(1)
    print(f'      Power Supply Voltage: {voltage}V')


def initialize(voltage):
    riden.set_v_set(voltage)
    riden.set_i_set(6)
    riden.set_output(1)
    print("      Power Supply On")


def close():
    riden.set_output(0)
    print("      Power Supply Off")

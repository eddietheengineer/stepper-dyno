import time
import numpy as np
from riden import Riden
riden = Riden(port="/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0",
              baudrate=115200, address=1)


def measure(sampleCount):
    start = time.perf_counter()
    measurements_power = []
    for _ in range(sampleCount):
        val = riden.get_p_out()
        measurements_power.append(val)
        time.sleep(0.1)
    filtered_data = reject_range_outliers(np.array(measurements_power))
    average_power = round(np.average(filtered_data), 2)
    powersupplytime = time.perf_counter() - start
    samples = len(filtered_data)
    return riden.get_v_out(), average_power, powersupplytime, samples


def summary(samples):
    [voltage_actual, power_actual, _, samples] = measure(samples)
    powersupply_data_label = ('v_supply', 'p_supply', 'p_samples')
    powersupply_data = (voltage_actual, power_actual, samples)
    return powersupply_data_label, powersupply_data


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

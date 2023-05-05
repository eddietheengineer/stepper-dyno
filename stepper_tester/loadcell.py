#! /usr/bin/python3
import time
import RPi.GPIO as GPIO
from hx711 import HX711
import numpy as np
from dataclasses import dataclass

@dataclass
class loadcelldata:
    grams: float
    capturetime: float
    samples: int

referenceunit = 1085
samplecount = 5

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceunit)


def close():
    print("      Cleaning Loadcell")
    GPIO.cleanup()


def tare():
    hx.reset()
    hx.tare()
    print("      Tared Loadcell")


def summary(speed, sampleCount):
    # Process Load Cell Data
    [grams, _, lc_samples] = measure(sampleCount)
    if grams < 0:
        grams = 0
    torque = grams / 1000 * 9.81 * 135 / 10
    motor_power = torque / 100 * speed * 2 * 3.1415/40
    mech_data_label = ('grams', 'torque',
                       'motor_power', 'lc_samples')
    mech_data = (round(grams, 3), round(torque, 3),
                 round(motor_power, 3), lc_samples)
    return mech_data_label, mech_data


def measure(sampleCount):
    start = time.perf_counter()
    measurements = []
    for _ in range(sampleCount):
        val = hx.get_weight(5)
        measurements.append(val)
        time.sleep(0.1)
    filtered_data = reject_range_outliers(np.array(measurements))
    loadcelldata.grams = np.average(filtered_data)
    loadcelldata.capturetime = round(time.perf_counter()-start,2)
    loadcelldata.samples = len(filtered_data)
    return loadcelldata


def reject_range_outliers(data, allowedrange=0.5):
    d = np.abs(data - np.median(data))
    return data[d < allowedrange]


def singleMeasure():
    measurement = hx.get_weight(5)
    return measurement

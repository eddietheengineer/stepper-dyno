#! /usr/bin/python3
import time
import RPi.GPIO as GPIO
from hx711 import HX711
import numpy as np
from dataclasses import dataclass

@dataclass
class loadcelldata:
    grams: float
    torque: float
    motorpower: float
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


def measure(sampleCount, speed):
    start = time.perf_counter()
    measurements = []
    for _ in range(sampleCount):
        val = hx.get_weight(5)
        measurements.append(val)
        time.sleep(0.1)
    filtered_data = reject_range_outliers(np.array(measurements))

    loadcelldata.grams = max(np.average(filtered_data),0)

    loadcelldata.torque = loadcelldata.grams / 1000 * 9.81 * 135 / 10
    loadcelldata.motorpower = loadcelldata.torque / 100 * speed * 2 * 3.1415/40
    loadcelldata.capturetime = round(time.perf_counter()-start,2)
    loadcelldata.samples = len(filtered_data)
    return loadcelldata


def reject_range_outliers(data, allowedrange=0.5):
    d = np.abs(data - np.median(data))
    return data[d < allowedrange]


def singleMeasure():
    measurement = hx.get_weight(5)
    return measurement

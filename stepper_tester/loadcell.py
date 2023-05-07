#! /usr/bin/python3
import time
import RPi.GPIO as GPIO
from hx711 import HX711
import numpy as np
from dataclasses import dataclass


@dataclass
class loadcelldata:
    grams: float = 0
    torque: float = 0
    motorpower: float = 0
    capturetime: float = 0
    samples: int = 0


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
    summary = loadcelldata()
    measurements = []
    for _ in range(sampleCount):
        val = hx.get_weight(5)
        measurements.append(val)
        time.sleep(0.1)
    filtered_data = reject_range_outliers(np.array(measurements))
    filtered_average = float(np.average(filtered_data))
    if (filtered_average is np.nan):
        summary.grams = max(round(float(np.average(measurements)),2),0)
        summary.samples = len(measurements)
    else:
        summary.grams = max(round(filtered_average,2),0)
        summary.samples = len(filtered_data)

    summary.torque = round(summary.grams / 1000 * 9.81 * 135 / 10, 2)
    summary.motorpower = round(summary.torque / 100 * speed * 2 * 3.1415/40, 2)
    summary.capturetime = round(time.perf_counter()-start, 2)
    return summary


def reject_range_outliers(data, allowedrange=0.5):
    d = np.abs(data - np.median(data))
    return data[d < allowedrange]


def singleMeasure():
    measurement = hx.get_weight(5)
    return measurement

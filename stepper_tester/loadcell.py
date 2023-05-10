#! /usr/bin/python3
import time
import RPi.GPIO as GPIO
from hx711 import HX711
import numpy as np
from dataclasses import dataclass


@dataclass
class loadcelldata:
    grams_array: np.ndarray = np.array([])
    grams: float = 0
    capturetime: float = 0
    samples: int = 0


referenceunit = 1085
hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceunit)


def measure(sampleCount):
    start = time.perf_counter()
    summary = loadcelldata()
    measurements = []
    for _ in range(sampleCount):
        val = hx.get_weight(5)
        measurements.append(val)
        time.sleep(0.1)
    summary.grams_array = np.array(measurements)
    filtered_data = reject_range_outliers(np.array(summary.grams_array))
    if (len(filtered_data) > 0):
        filtered_average = float(np.average(filtered_data))
        summary.grams = max(round(float(np.average(filtered_average)), 2), 0)
        summary.samples = len(filtered_data)

    summary.capturetime = round(time.perf_counter()-start, 2)
    return summary


def reject_range_outliers(data, allowedrange=0.5):
    d = np.abs(data - np.median(data))
    return data[d < allowedrange]


def close():
    print("      Cleaning Loadcell")
    GPIO.cleanup()


def tare():
    hx.reset()
    hx.tare()
    print("      Tared Loadcell")

#! /usr/bin/python3
import time
import sys
import RPi.GPIO as GPIO
from hx711 import HX711
import numpy as np

referenceUnit = 1085
sampleCount = 5

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()

def close():
    print("      Cleaning Loadcell")
    GPIO.cleanup()
    
def tare():
	hx.reset()
	hx.tare()
	print("      Tared Loadcell")

def measure(sampleCount):
	start = time.perf_counter()
	measurements = []
	for x in range(sampleCount):
		val = hx.get_weight(5)
		measurements.append(val)
		time.sleep(0.1)
	filtered_data = reject_range_outliers(np.array(measurements))
	average = np.average(filtered_data)
	return average
    
def reject_range_outliers(data, range=0.5):
    d = np.abs(data - np.median(data))
    return data[d < range]
	
def singleMeasure():
	measurement = hx.get_weight(5)
	return measurement

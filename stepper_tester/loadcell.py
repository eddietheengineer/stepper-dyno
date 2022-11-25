#! /usr/bin/python3
import time
import sys
import RPi.GPIO as GPIO
from hx711 import HX711

referenceUnit = 1085
sampleCount = 5

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")
hx.set_reference_unit(referenceUnit)
hx.reset()

def close():
    print("Cleaning Loadcell")
    GPIO.cleanup()
    
def tare():
	hx.reset()
	hx.tare()
	print("Tared Loadcell")

def measure(sampleCount):
	total = 0
	for x in range(sampleCount):
		val = hx.get_weight(5)
		total = val + total
		#hx.power_down()
		#hx.power_up()
		time.sleep(0.1)
	measurement = total / sampleCount
	return measurement
	#print("Load Cell Measurement")
	
def singleMeasure():
	measurement = hx.get_weight(5)
	return measurement
	#print("Load Cell Measurement")
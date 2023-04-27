import pyvisa as visa
import numpy as np
import math as math
import time
import sys
import re

TEST_CHANNEL = 2

try:
    rm = visa.ResourceManager()
    # Connect to device (Make sure to change the resource locator!)
    device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    #device = rm.open_resource('TCPIP::10.10.10.163::INSTR',query_delay=0.25)

except:
    print('      Failed to connect to oscilloscope')
    sys.exit(0)
device.timeout = 5000

device.write(f'C{TEST_CHANNEL}:TRACE ON')

#Set Trigger Mode
device.write(f'TRIG_MODE NORM')
#Set Trigger Level to 0V
device.write(f'C{TEST_CHANNEL}:TRIG_LEVEL 100mV')
#Set Trigger Coupling to AC
device.write(f'C{TEST_CHANNEL}:TRIG_COUPLING DC')
#Set Trigger Select to EDGE and Current Channel
device.write(f'TRIG_SELECT EDGE, SR, C{TEST_CHANNEL}')
#Set Trigger Slope Positive
device.write(f'C{TEST_CHANNEL}:TRIG_SLOPE POS')

def parseOscilloscopeResponse(response):
	#match = re.search(r'\s([-+]?\d*\.\d+(?:[Ee][-+]?\d+)?)\w', response)
	#match = re.search(r'\s([-+]?\d*\.?\d+(?:[eE][-+]?\d+))', response)
	#rmsVoltage
	match = re.search(r'([-+]?\d*\.\d+([eE][-+]?\d+)?)', response)

	if match:
		processedResponse = float(match.group(1))
	else:
		processedResponse = None
	return processedResponse
	
def setup(Samples):	
	#send capture to controller
	Sparsing = 1
	device.write(str.format(f'WAVEFORM_SETUP SP,{Sparsing},NP,{Samples},FP,0'))

def write():
	device.write(str.format('C2:WAVEFORM? DAT2'))
	device.chunk_size = 1024

def collect():
	# read capture from controller
	device.write('C2:WAVEFORM? DAT2')
	TEMP = device.read_raw()
	print(TEMP)
	print(TEMP[-4:-1])

	
def all(Samples):
	setup(Samples)
	write()
	wf = collect()
	return wf
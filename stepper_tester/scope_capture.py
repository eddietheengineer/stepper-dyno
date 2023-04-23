import pyvisa as visa
import numpy as np
import math as math
import time
import sys
import re

TOTAL_CHANNELS = 4
CURRENT_CHANNEL = 3
VOLTAGE_CHANNEL = 1

#Oscilloscope Settings:
global TIME_DIV
TIME_DIV = 0
global TRIG_DELAY
TRIG_DELAY = 0
global VOLT_DIV
VOLT_DIV = 0
global AMP_DIV
AMP_DIV = 0
global MATH_DIV
MATH_DIV = 0
global VOLT_OFFSET
VOLT_OFFSET = 0
global AMP_OFFSET
AMP_OFFSET = 0
global MATH_OFFSET
MATH_OFFSET = 0



try:
    rm = visa.ResourceManager()
    # Connect to device (Make sure to change the resource locator!)
    #device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    device = rm.open_resource('TCPIP::10.10.10.163::INSTR',query_delay=0.25)

except:
    print('      Failed to connect to oscilloscope')
    sys.exit(0)
device.timeout = 30000

def startChannels():
	for i in range(1,TOTAL_CHANNELS+1):		
		if((i == CURRENT_CHANNEL)|(i == VOLTAGE_CHANNEL)):
			device.write(f'C{i}:TRACE ON')
			#print(f'{i} is ON')
		else:
			device.write(f'C{i}:TRACE OFF')
			#print(f'{i} is OFF')
	
def setupScope():
	print('      Connected to Oscilloscope')
	startChannels()
	
	#use sampling instead of average
	device.write('ACQUIRE_WAY SAMPLING')

	#Set Trigger Mode
	device.write('TRIG_MODE NORM')
	#Set Trigger Level to 0V
	device.write('C{CURRENT_CHANNEL}:TRIG_LEVEL 100mV')
	#Set Trigger Coupling to AC
	device.write('C{CURRENT_CHANNEL}:TRIG_COUPLING DC')
	#Set Trigger Select to EDGE and Current Channel
	device.write(f'TRIG_SELECT EDGE, SR, C{CURRENT_CHANNEL}')
	#Set Trigger Slope Positive
	device.write(f'C{CURRENT_CHANNEL}:TRIG_SLOPE POS')
	
	#set memory depth to 14M Samples
	device.write('MEMORY_SIZE 14M')
	#Turn Off Persistent Display
	device.write('PERSIST OFF')
	
	#Set Voltage Channel to Volts
	device.write(f'C{VOLTAGE_CHANNEL}:UNIT V')
	#Set Voltage Channel to 10X
	device.write(f'C{VOLTAGE_CHANNEL}:ATTENUATION 10')
	#Set Voltage Channel to DC Coupling
	device.write(f'C{VOLTAGE_CHANNEL}:COUPLING D1M')
	#Set Voltage Channel Vertical Offset to 0
	device.write(f'C{VOLTAGE_CHANNEL}:OFFSET {VOLT_OFFSET}V')
	
	#Set Current Channel to Amps
	device.write(f'C{CURRENT_CHANNEL}:UNIT A')
	#Set Current Channel to 10X
	device.write(f'C{CURRENT_CHANNEL}:ATTENUATION 10')
	#Set Current Channel to DC Coupling
	device.write(f'C{CURRENT_CHANNEL}:COUPLING D1M')
	#Set Current Channel Vertical Offset to 0V
	device.write(f'C{CURRENT_CHANNEL}:OFFSET {AMP_OFFSET}V')
	
	#Set Math Vertical Offset to 0V
	device.write('MATH_VERT_POS {MATH_OFFSET}')
	
	#Set Buzzer Off
	device.write('BUZZER OFF')
	
	parameterMeasureStart()
		
def configureScopeHorizontalAxis(CaptureTime_us):
	global TIME_DIV
	global TRIG_DELAY
	#Supported Configurations for Siglent SDS1104
	TimePerDivisionOptions_us  = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000,100000]

	#Display is 14 sections wide
	TimePerDivisionRaw_us = CaptureTime_us / 14
	
	#Find closest option available to raw value
	[x, TimePerDivision_us] = findFirstInstanceGreaterThan(TimePerDivisionOptions_us, TimePerDivisionRaw_us)

	#Set Trigger Delay so T=0 is on left of screen
	TriggerDelay_us = -TimePerDivision_us*7

	#Write configuration parameters to Oscilloscope if changed
	if(TimePerDivision_us != TIME_DIV):
		device.write(f'TIME_DIV {TimePerDivision_us}US')
		device.write(f'TRIG_DELAY {TriggerDelay_us}US')
		TIME_DIV = TimePerDivision_us
		TRIG_DELAY = TriggerDelay_us
	
def configureScopeVerticalAxis(inputVoltage, targetCurrentRms):
	global VOLT_DIV
	global AMP_DIV
	global MATH_DIV
	
	#Volts -> mV -> 4 sections -> 200% of data
	VoltsPerDivision_V = math.ceil(inputVoltage/4*2)
	if(VoltsPerDivision_V != VOLT_DIV):
		device.write(f'C{VOLTAGE_CHANNEL}:VOLT_DIV {VoltsPerDivision_V}V')
		print(f'      Updated VOLT DIV Old:{VOLT_DIV}, New:{VoltsPerDivision_V}')
		VOLT_DIV = VoltsPerDivision_V
	
	#Amps -> A -> 4 sections -> Arms to Apkpk -> 150% of data
	AmpsPerDivision_A = math.ceil(targetCurrentRms*10/4*1.4*1.5)/10
	if(AmpsPerDivision_A != AMP_DIV):
		device.write(f'C{CURRENT_CHANNEL}:VOLT_DIV {AmpsPerDivision_A*1000}mV')	
		print(f'      Updated AMP DIV Old:{AMP_DIV}, New:{AmpsPerDivision_A}')
		AMP_DIV = AmpsPerDivision_A
	
	#Power -> W -> 4 sections -> inputVoltage * targetCurrentRMS *  -> 150% of data
	MathDivOptions_W = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000]
	MathPerDivisionRaw = math.ceil(AmpsPerDivision_A * VoltsPerDivision_V * 2)
	[x, MathPerDivision] = findFirstInstanceGreaterThan(MathDivOptions_W, MathPerDivisionRaw)

	if(MathPerDivision != MATH_DIV):
		device.write(f'MATH_VERT_DIV {MathPerDivision}V')	
		print(f'      Updated MATH DIV Old:{MATH_DIV}, New: {MathPerDivision}')
		MATH_DIV = MathPerDivision
	
def findFirstInstanceGreaterThan(array, value):
	for x in range(len(array)):
		if array[x] > value:
			return [x, array[x]]
			break

def findClosestValue(array, value):
	array = np.asarray(array)
	idx = (np.abs(array-value)).argmin()
	return [idx, array[idx]]

def captureAllSingle(Samples,Time_Scale,V_Set,A_Set):
	global VOLT_DIV
	global VOLT_OFFSET

	global AMP_DIV
	global AMP_OFFSET

	global MATH_DIV
	global MATH_OFFSET

	global TIME_DIV
	global TRIG_DELAY
	
	start_time = time.perf_counter()
	
	configureScopeHorizontalAxis(Time_Scale)
	
	#configureScopeVerticalAxis(V_Set,A_Set)	
	
	Channel_Split = 1
	if(TIME_DIV == 5000):
		Sparsing = np.ceil(Time_Scale/(Samples/200))/Channel_Split
	elif(TIME_DIV == 2000):
		Sparsing = np.ceil(Time_Scale/(Samples/500))/Channel_Split
	else:
		Sparsing = np.ceil(Time_Scale/(Samples/1000))/Channel_Split
		
	# Setup waveform capture
	device.write(str.format(f'WAVEFORM_SETUP SP,{Sparsing},NP,{Samples},FP,0'))

	#Start Capture
	device.write('ARM')
	device.write('WAIT')
	time.sleep(0.5)
	
	################# Capture Data #################
	VOLTAGE_WAVEFORM = []
	CURRENT_WAVEFORM = []
	MATH_WAVEFORM = []
	i = 0
	while ((len(VOLTAGE_WAVEFORM) != len(CURRENT_WAVEFORM)) | (len(VOLTAGE_WAVEFORM) == 0)):
		[VOLTAGE_WAVEFORM, CURRENT_WAVEFORM, MATH_WAVEFORM] = collectOscilloscopeData()
		if(len(VOLTAGE_WAVEFORM) == 0 & i < 5):
			print('Missed Data')
			i += 1

	################# VOLTAGE PROCESS #################
	VOLTAGE_RESULT = []
	#convert raw data to voltage, P142 in prog manual
	for item in VOLTAGE_WAVEFORM:
		if item > 127:
			VOLTAGE_RESULT.append((item - 255) * (VOLT_DIV/25) - VOLT_OFFSET)
		else:
			VOLTAGE_RESULT.append(item * VOLT_DIV/25 - VOLT_OFFSET)
							
	################# CURRENT PROCESS #################		
	CURRENT_RESULT = []
	#convert raw data to voltage, P142 in prog manual
	for item in CURRENT_WAVEFORM:
		if item > 127:
			CURRENT_RESULT.append((item - 255) * (AMP_DIV/25) - AMP_OFFSET)
		else:
			CURRENT_RESULT.append(item * AMP_DIV/25 - AMP_OFFSET)
			
			
	################# MATH PROCESS #################
	MATH_RESULT = []
	#convert raw data to voltage, P142 in prog manual
	for item in MATH_WAVEFORM:
		if item > 127:
			MATH_RESULT.append((item - 255) * (MATH_DIV/25) - MATH_OFFSET)
		else:
			MATH_RESULT.append(item * MATH_DIV/25 - MATH_OFFSET)
			
				      
	################# TIME PROCESS #################	
	SAMPLE_RATE = device.query('SAMPLE_RATE?')
	SAMPLE_RATE = float(SAMPLE_RATE[len('SARA '):-5])
	Time_Interval = 1 / SAMPLE_RATE

	#get time interval, P143 in prog manual
	Initial_Time_Value = TRIG_DELAY + (TIME_DIV * 14/2)
		
	#build time axis array
	TIME_AXIS = []
	for i in range(len(VOLTAGE_RESULT)):
		if i ==0:
			TIME_AXIS.append(Initial_Time_Value)
		elif i > 0:
			TIME_AXIS.append(TIME_AXIS[0] + (Time_Interval * Sparsing)*i)
	TIME_AXIS = np.array(TIME_AXIS)
	
	#Combine data into one array
	oscilloscope_raw_data = np.stack((TIME_AXIS, VOLTAGE_RESULT, CURRENT_RESULT, MATH_RESULT), axis=0)
	
	#Trim to length of one cycle
	[idx_start, val] = findClosestValue(oscilloscope_raw_data[0], 0)
	[idx_end, val] = findClosestValue(oscilloscope_raw_data[0], (Initial_Time_Value + Time_Scale/1000))
	oscilloscope_trim_data = oscilloscope_raw_data[:,idx_start:idx_end]
	print(f'      OS Time: {time.perf_counter() - start_time:0.2f}')

	parameterMeasureRead()
	return oscilloscope_trim_data
	
def collectOscilloscopeData():	
	#send capture to controller
	device.write(str.format(f'C{CURRENT_CHANNEL}:WAVEFORM? DAT2'))
	device.write(str.format(f'C{VOLTAGE_CHANNEL}:WAVEFORM? DAT2'))
	device.chunk_size = 1024*1024*1024

	# read capture from controller
	VOLTAGE_WAVEFORM = device.query_binary_values(str.format(f'C{VOLTAGE_CHANNEL}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
	CURRENT_WAVEFORM = device.query_binary_values(str.format(f'C{CURRENT_CHANNEL}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
	POWER_WAVEFORM = device.query_binary_values(str.format(f'MATH:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
	return VOLTAGE_WAVEFORM, CURRENT_WAVEFORM, POWER_WAVEFORM
	
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
	 	
# def generateTimeAxis(Samples, Sparsing):
# 	##########Generate Time Scale################
# 	#Find Time at Center of Screen
# 	TrigDelay_ns = parseOsilloscopeResponse(device.query('TRIG_DELAY?'))
# 	
# 	#Find Current Time Base
# 	TimeDiv_s = parseOscilloscopeResponse(device.query('TIME_DIV?'))
# 	
# 	#Find Sampling Rate:
# 	SamplingRate_GSas = parseOscilloscopeResponse(device.query('SAMPLE_RATE?'))
# 	
# 	#Calculate time value of first data point (Programming Guide p143)
# 	TimeValueStart_ns = TrigDelay_ns - (TimeDiv_s * 10^9 * 14/2)
# 	
# 	SampleTimeInterval_ns = 1/SamplingRate_Gsas
# 	
# 	TimeArray = []
# 	for i in range(0,Samples):
# 		if i == 0:
# 			TimeArray.append(TimeValueStart_ns)
# 		elif i > 0:
# 			TimeArray.append(TimeArray[0] + (TimeDiv * Sparsing)*i)
# 	TimeArray = np.array(TimeArray)*1000
# 	return TimeArray
 	
def parameterMeasureStart():
	#Set Up Voltage Measurement
	device.write('PARAMETER_CLR')
	
	device.write(f'PARAMETER_CUSTOM RMS, C{VOLTAGE_CHANNEL}')
	device.write(f'PARAMETER_CUSTOM PKPK, C{VOLTAGE_CHANNEL}')
	
	#Set Up Current measurement:
	device.write(f'PARAMETER_CUSTOM RMS, C{CURRENT_CHANNEL}')
	device.write(f'PARAMETER_CUSTOM PKPK, C{CURRENT_CHANNEL}')
		
	#Set Up Math Measurement
	device.write("'DEFINE_EQN, 'C1*C3'")

def parameterMeasureRead():
	#Read Voltage
	volt_rms = parseOscilloscopeResponse(device.query(f'C{VOLTAGE_CHANNEL}:PARAMETER_VALUE? RMS'))
	volt_pk = parseOscilloscopeResponse(device.query(f'C{VOLTAGE_CHANNEL}:PARAMETER_VALUE? PKPK'))
	
	#Read Current
	current_rms = parseOscilloscopeResponse(device.query(f'C{CURRENT_CHANNEL}:PARAMETER_VALUE? RMS'))
	current_pk = parseOscilloscopeResponse(device.query(f'C{CURRENT_CHANNEL}:PARAMETER_VALUE? PKPK'))
	return round(volt_rms,1), round(volt_pk,1), round(current_rms,3), round(current_pk,3)
	
setupScope()

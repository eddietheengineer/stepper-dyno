import pyvisa as visa
import numpy as np
import time
import sys
import re

TOTAL_CHANNELS = 4
CURRENT_CHANNEL = 3
VOLTAGE_CHANNEL = 1

try:
    rm = visa.ResourceManager()
    # Connect to device (Make sure to change the resource locator!)
    #device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    device = rm.open_resource('TCPIP::10.10.10.163::INSTR',query_delay=0.25)

except:
    print('Failed to connect to oscilloscope')
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
	print('Connected to oscilloscope')
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
	device.write(f'C{VOLTAGE_CHANNEL}:OFFSET 0V')
	
	#Set Current Channel to Amps
	device.write(f'C{CURRENT_CHANNEL}:UNIT A')
	#Set Current Channel to 10X
	device.write(f'C{CURRENT_CHANNEL}:ATTENUATION 10')
	#Set Current Channel to DC Coupling
	device.write(f'C{CURRENT_CHANNEL}:COUPLING D1M')
	#Set Current Channel Vertical Offset to 0V
	device.write(f'C{CURRENT_CHANNEL}:OFFSET 0V')
	
	parameterMeasureStart()
		
def configureScopeHorizontalAxis(CaptureTime_us):
	#Supported Configurations for Siglent SDS1104
	TimePerDivisionOptions_us  = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000,100000]

	#Display is 14 sections wide
	TimePerDivisionRaw_us = CaptureTime_us / 14
	
	#Find closest option available to raw value
	[x, TimePerDivision_us] = findFirstInstanceGreaterThan(TimePerDivisionOptions_us, TimePerDivisionRaw_us)

	#Set Trigger Delay so T=0 is on left of screen
	TriggerDelay_us = -TimePerDivision_us*7
	
	#Write configuration parameters to Oscilloscope
	device.write(f'TIME_DIV {TimePerDivision_us}US')
	device.write(f'TRIG_DELAY {TriggerDelay_us}US')
	return TimePerDivision_us
	
def configureScopeVerticalAxis(inputVoltage, targetCurrentRms):
	#Volts -> mV -> 4 sections -> 200% of data
	VoltagePerDivision_mV = round(inputVoltage*1000/4*2)
	device.write(f'C{VOLTAGE_CHANNEL}:VOLT_DIV {VoltagePerDivision_mV}MV')
	
	#Amps -> mA -> 4 sections -> Arms to Apkpk -> 150% of data
	AmpsPerDivision_mA = round(targetCurrentRms*1000/4*1.4*1.5)
	device.write(f'C{CURRENT_CHANNEL}:VOLT_DIV {AmpsPerDivision_mA}MV')	
	
	#Power -> W -> 4 sections -> inputVoltage * targetCurrentRMS *  -> 150% of data
	#AmpsPerDivision_mA = round(targetCurrentRms*1000/4*1.4*1.5)
	#device.write(f'C{CURRENT_CHANNEL}:VOLT_DIV {AmpsPerDivision_mA}MV')	
	
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
	u_sec_set = configureScopeHorizontalAxis(Time_Scale)
	configureScopeVerticalAxis(V_Set,A_Set)
	TIME_DIV = u_sec_set/1000000
	Channel_Split = 1
	
	if(u_sec_set == 5000):
		Sparsing = np.ceil(Time_Scale/(Samples/200))/Channel_Split
	elif(u_sec_set == 2000):
		Sparsing = np.ceil(Time_Scale/(Samples/500))/Channel_Split
	else:
		Sparsing = np.ceil(Time_Scale/(Samples/1000))/Channel_Split
	
	VOLT_DIV_RAW = device.query(str.format(f'C{VOLTAGE_CHANNEL}:VOLT_DIV?'))
	#print(VOLT_DIV_RAW)
	VOLT_DIV = float(VOLT_DIV_RAW[len(str.format(f'C{VOLTAGE_CHANNEL}:VDIV ')):-2])
	#print(VOLT_DIV)
	
	VOLT_OFFSET = device.query(str.format(f'C{VOLTAGE_CHANNEL}:OFFSET?'))
	VOLT_OFFSET = float(VOLT_OFFSET[len(str.format(f'C{VOLTAGE_CHANNEL}:OFST ')):-2])
	
	CURRENT_DIV = device.query(str.format(f'C{CURRENT_CHANNEL}:VOLT_DIV?'))
	CURRENT_DIV = float(CURRENT_DIV[len(str.format(f'C{CURRENT_CHANNEL}:VDIV ')):-2])
	
	CURRENT_OFFSET = device.query(str.format(f'C{CURRENT_CHANNEL}:OFFSET?'))
	CURRENT_OFFSET = float(CURRENT_OFFSET[len(str.format(f'C{CURRENT_CHANNEL}:OFST ')):-2])
	
	MATH_DIV = device.query(str.format('MATH_VERT_DIV?'))
	MATH_DIV = parseOscilloscopeResponse(MATH_DIV)
	
	MATH_OFFSET = device.query(str.format('MATH_VERT_POS?'))
	MATH_OFFSET = float(MATH_OFFSET[len(str.format('MTVP ')):-1])
	
	SAMPLE_RATE = device.query('SAMPLE_RATE?')
	SAMPLE_RATE = float(SAMPLE_RATE[len('SARA '):-5])

	TRIG_DELAY = device.query('TRIG_DELAY?')
	TRIG_DELAY = -float(TRIG_DELAY[len('TRDL '):-2])

	#get time interval, P143 in prog manual
	TIME_VALUE = TRIG_DELAY - (TIME_DIV * 14/2)
	TIME_INTERVAL = 1 / SAMPLE_RATE
	
	# Setup waveform capture
	device.write(str.format(f'WAVEFORM_SETUP SP,{Sparsing},NP,{Samples},FP,0'))

	#Start Capture
	device.write('ARM')
	device.write('WAIT')
	time.sleep(0.5)
	
	################# Capture Data #################
	VOLTAGE_WAVEFORM = []
	CURRENT_WAVEFORM = []
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
			CURRENT_RESULT.append((item - 255) * (CURRENT_DIV/25) - CURRENT_OFFSET)
		else:
			CURRENT_RESULT.append(item * CURRENT_DIV/25 - CURRENT_OFFSET)
			
	################# MATH PROCESS #################		
	MATH_RESULT = []
	#convert raw data to voltage, P142 in prog manual
	for item in MATH_WAVEFORM:
		if item > 127:
			MATH_RESULT.append((item - 255) * (MATH_DIV/25) - MATH_OFFSET)
		else:
			MATH_RESULT.append(item * MATH_DIV/25 - MATH_OFFSET)
			      
	################# TIME PROCESS #################		
	#build time axis array
	TIME_AXIS = []
	for i in range(len(VOLTAGE_RESULT)):
		if i ==0:
			TIME_AXIS.append(TIME_VALUE)
		elif i > 0:
			TIME_AXIS.append(TIME_AXIS[0] + (TIME_INTERVAL * Sparsing)*i)
	TIME_AXIS = np.array(TIME_AXIS)*1000
	
	#Combine data into one array
	oscilloscope_raw_data = np.stack((TIME_AXIS, VOLTAGE_RESULT, CURRENT_RESULT, MATH_RESULT), axis=0)
	
	#Trim to length of one cycle
	[idx_start, val] = findClosestValue(oscilloscope_raw_data[0], 0)
	[idx_end, val] = findClosestValue(oscilloscope_raw_data[0], (TIME_VALUE + Time_Scale/1000))
	#print(val - Time_Scale/1000)
	oscilloscope_trim_data = oscilloscope_raw_data[:,idx_start:idx_end]
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
		#print(match.group(1))
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
	return volt_rms, volt_pk, current_rms, current_pk
	
setupScope()

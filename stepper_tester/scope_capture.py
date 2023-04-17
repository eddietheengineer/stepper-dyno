import pyvisa as visa
import numpy as np
import time
import sys

TOTAL_CHANNELS = 4
CURRENT_CHANNEL = 3
VOLTAGE_CHANNEL = 1

try:
    rm = visa.ResourceManager()
    # Connect to device (Make sure to change the resource locator!)
    #device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    device = rm.open_resource('TCPIP::10.10.10.163::INSTR',query_delay=0.25)

except:
    print('Failed to connect to device...')
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

	startChannels()
	
	#use sampling instead of average
	device.write('ACQUIRE_WAY SAMPLING')

	#Set Trigger Mode
	device.write('TRIG_MODE NORM')
	#Set Trigger Level to 0V
	device.write('C{CURRENT_CHANNEL}:TRIG_LEVEL 0V')
	#Set Trigger Coupling to AC
	device.write('C{CURRENT_CHANNEL}:TRIG_COUPLING AC')
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
	
setupScope()



	
def configureScopeHorizontalAxis(Time_Range):
	U_sec = Time_Range / 7
	U_sec_array  = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000,100000]
	[idx, U_sec_set] = find_nearest(U_sec_array, U_sec)
	#U_sec_set = round(U_sec)
	Trig_delay = -U_sec_set*7
	device.write('TIME_DIV %dUS' % U_sec_set)
	device.write('TRIG_DELAY %dUS' % Trig_delay)
	return U_sec_set
	
def configureScopeVerticalAxis(inputVoltage, inputCurrent):
	volt_div_array = [2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000,100000]
	print(inputVoltage, inputCurrent)
	#[idx, mvVoltDivSet] = find_nearest(volt_div_array, inputVoltage*1000/4*1.5)
	mvVoltDivSet = round(inputVoltage*1000/4*1.5)
	device.write(f'C{VOLTAGE_CHANNEL}:VOLT_DIV {mvVoltDivSet}MV')
	#[idx, mvAmpDivSet] = find_nearest(volt_div_array, inputCurrent*1000/4*1.4*1.5)
	mvAmpDivSet = round(inputCurrent*1000/4*1.4*1.5)
	device.write(f'C{CURRENT_CHANNEL}:VOLT_DIV {mvAmpDivSet}MV')	
	print(mvVoltDivSet, mvAmpDivSet)

def find_nearest(array, value):
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
	
	VOLT_DIV = device.query(str.format(f'C{VOLTAGE_CHANNEL}:VOLT_DIV?'))
	VOLT_DIV = float(VOLT_DIV[len(str.format(f'C{VOLTAGE_CHANNEL}:VDIV ')):-2])
	
	VOLT_OFFSET = device.query(str.format(f'C{VOLTAGE_CHANNEL}:OFFSET?'))
	VOLT_OFFSET = float(VOLT_OFFSET[len(str.format(f'C{VOLTAGE_CHANNEL}:OFST ')):-2])
	
	CURRENT_DIV = device.query(str.format(f'C{CURRENT_CHANNEL}:VOLT_DIV?'))
	CURRENT_DIV = float(CURRENT_DIV[len(str.format(f'C{CURRENT_CHANNEL}:VDIV ')):-2])
	
	CURRENT_OFFSET = device.query(str.format(f'C{CURRENT_CHANNEL}:OFFSET?'))
	CURRENT_OFFSET = float(CURRENT_OFFSET[len(str.format(f'C{CURRENT_CHANNEL}:OFST ')):-2])
	
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
	
	#Sanity Check Data - make sure data collected before processing
	VOLTAGE_WAVEFORM = []
	CURRENT_WAVEFORM = []
	while ((len(VOLTAGE_WAVEFORM) != len(CURRENT_WAVEFORM)) | (len(VOLTAGE_WAVEFORM) == 0)):
		[VOLTAGE_WAVEFORM, CURRENT_WAVEFORM] = collectOscilloscopeData()
		if(len(VOLTAGE_WAVEFORM) == 0):
			print('Missed Data')

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
			      
	################# TIME PROCESS #################		
	#build time axis array
	TIME_AXIS = []
	for i in range(len(VOLTAGE_RESULT)):
		if i ==0:
			TIME_AXIS.append(TIME_VALUE)
		elif i > 0:
			TIME_AXIS.append(TIME_AXIS[0] + (TIME_INTERVAL * Sparsing)*i)
	TIME_AXIS = np.array(TIME_AXIS)*1000
	
	#Trim to length of one cycle
	oscilloscope_raw_data = np.stack((TIME_AXIS, VOLTAGE_RESULT, CURRENT_RESULT), axis=0)
	[idx_start, val] = find_nearest(oscilloscope_raw_data[0], 0)
	[idx_end, val] = find_nearest(oscilloscope_raw_data[0], Time_Scale/1000)
	oscilloscope_trim_data = oscilloscope_raw_data[:,idx_start:idx_end]
	
	return oscilloscope_trim_data
	
	
def collectOscilloscopeData():	
	#send capture to controller
	device.write(str.format(f'C{CURRENT_CHANNEL}:WAVEFORM? DAT2'))
	device.write(str.format(f'C{VOLTAGE_CHANNEL}:WAVEFORM? DAT2'))
	device.chunk_size = 1024*1024*1024

	# read capture from controller
	VOLTAGE_WAVEFORM = device.query_binary_values(str.format(f'C{VOLTAGE_CHANNEL}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
	CURRENT_WAVEFORM = device.query_binary_values(str.format(f'C{CURRENT_CHANNEL}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
	return VOLTAGE_WAVEFORM, CURRENT_WAVEFORM
	
def captureAllSingleV2(Samples,Time_Scale):
	u_sec_set = configureScopeHorizontalAxis(Time_Scale)
	TIME_DIV = u_sec_set/1000000
	Channel_Split = 1
	
	if(u_sec_set == 5000):
		Sparsing = np.ceil(Time_Scale/(Samples/200))/Channel_Split
	elif(u_sec_set == 2000):
		Sparsing = np.ceil(Time_Scale/(Samples/500))/Channel_Split
	else:
		Sparsing = np.ceil(Time_Scale/(Samples/1000))/Channel_Split
	
	VOLT_DIV = device.query(str.format(f'C{VOLTAGE_CHANNEL}:VOLT_DIV?'))
	VOLT_DIV = float(VOLT_DIV[len(str.format(f'C{VOLTAGE_CHANNEL}:VOLT_DIV')):-2])
	
	VOLT_OFFSET = device.query(str.format(f'C{VOLTAGE_CHANNEL}:OFFSET?'))
	VOLT_OFFSET = float(VOLT_OFFSET[len(str.format(f'C{VOLTAGE_CHANNEL}:OFFSET')):-2])
	
	CURRENT_DIV = device.query(str.format(f'C{CURRENT_CHANNEL}:VOLT_DIV?'))
	CURRENT_DIV = float(CURRENT_DIV[len(str.format(f'C{CURRENT_CHANNEL}:VOLT_DIV')):-2])
	
	CURRENT_OFFSET = device.query(str.format(f'C{CURRENT_CHANNEL}:OFFSET?'))
	CURRENT_OFFSET = float(CURRENT_OFFSET[len(str.format(f'C{CURRENT_CHANNEL}:OFFSET')):-2])
	
	SAMPLE_RATE = device.query('SARA?')
	SAMPLE_RATE = float(SAMPLE_RATE[len('SARA '):-5])

	TRIG_DELAY = device.query('TRDL?')
	TRIG_DELAY = -float(TRIG_DELAY[len('TRDL '):-2])

	#get time interval, P143 in prog manual
	TIME_VALUE = TRIG_DELAY - (TIME_DIV * 14/2)
	TIME_INTERVAL = 1 / SAMPLE_RATE
	
	################# VOLTAGE CAPTURE #################
	# Setup waveform capture
	device.write(str.format(f'WAVEFORM_SETUP SP,{Sparsing},NP,{Samples},FP,0'))
		
	#send capture to controller
	device.write(str.format(f'C{VOLTAGE_CHANNEL}:WAVEFORM? DAT2'))
	device.chunk_size = 1024*1024*1024
	
	#Arm Oscilloscope
	#device.write('ARM')

	# read capture from controller
	WAVEFORM = device.query_binary_values(str.format(f'C{VOLTAGE_CHANNEL}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
	RESULT = []
	#convert raw data to voltage, P142 in prog manual
	for item in WAVEFORM:
		if item > 127:
			RESULT.append((item - 255) * (VOLT_DIV/25) - VOLT_OFFSET)
		else:
			RESULT.append(item * VOLT_DIV/25 - VOLT_OFFSET)
			
	print(len(RESULT))
	
	################# CURRENT CAPTURE #################
	# Setup waveform capture
	device.write(str.format(f'WAVEFORM_SETUP SP,{Sparsing},NP,{Samples},FP,0'))
		
	#send capture to controller
	device.write(str.format(f'C{CURRENT_CHANNEL}:WAVEFORM? DAT2'))
	device.chunk_size = 1024*1024*1024
	
	#Arm Oscilloscope
	#device.write('ARM')

	# read capture from controller
	WAVEFORM1 = device.query_binary_values(str.format(f'C{CURRENT_CHANNEL}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
	RESULT1 = []
	#convert raw data to voltage, P142 in prog manual
	for item in WAVEFORM1:
		if item > 127:
			RESULT1.append((item - 255) * (CURRENT_DIV/25) - CURRENT_OFFSET)
		else:
			RESULT1.append(item * CURRENT_DIV/25 - CURRENT_OFFSET)
			
	print(len(RESULT1))
        
	#build time axis array
	TIME_AXIS = []
	for i in range(len(RESULT)):
		if i ==0:
			TIME_AXIS.append(TIME_VALUE)
		elif i > 0:
			TIME_AXIS.append(TIME_AXIS[0] + (TIME_INTERVAL * Sparsing)*i)
	TIME_AXIS = np.array(TIME_AXIS)*1000
	
	oscilloscope_raw_data = np.stack((TIME_AXIS, RESULT, RESULT1), axis=0)
	
	#[idx_start, val] = find_nearest(oscilloscope_raw_data[0], 0)
	
	#[idx_end, val] = find_nearest(oscilloscope_raw_data[0], Time_Scale/1000)
	
	#oscilloscope_trim_data = oscilloscope_raw_data[:,idx_start:idx_end]
	
	#return oscilloscope_trim_data
	return oscilloscope_raw_data
def captureAll(Samples,Time_Scale):
	u_sec_set = configureScopeHorizontalAxis(Time_Scale)
	#TIME_DIV = device.query('TDIV?')
	#TIME_DIV = float(TIME_DIV[len('TDIV '):-2])
	TIME_DIV = u_sec_set/1000000
	Channel_Split = 1
	
	if(u_sec_set == 5000):
		Sparsing = np.ceil(Time_Scale/(Samples/200))/Channel_Split
	elif(u_sec_set == 2000):
		Sparsing = np.ceil(Time_Scale/(Samples/500))/Channel_Split
	else:
		Sparsing = np.ceil(Time_Scale/(Samples/1000))/Channel_Split
	
	Channel = 1
	VOLT_DIV = device.query(str.format('C%s:Volt_DIV?' % Channel))
	VOLT_DIV = float(VOLT_DIV[len(str.format('C%s:VDIV ' % Channel)):-2])
	
	VOLT_OFFSET = device.query(str.format('C%s:OFfSeT?' % Channel))
	VOLT_OFFSET = float(VOLT_OFFSET[len(str.format('C%s:OFST ' % Channel)):-2])

	# Setup waveform capture
	device.write(str.format('WFSU SP,%d,NP,%d,FP,0' % (Sparsing, Samples)))
	
	device.write('ARM')
	
	#send capture to controller
	device.write(str.format('C%d:WF? DAT2' % Channel))
	device.chunk_size = 1024*1024*1024

	# read capture from controller
	WAVEFORM = device.query_binary_values(str.format('C%d:WF? DAT2' % Channel), datatype='s', is_big_endian=False)
	RESULT = []
	#convert raw data to voltage, P142 in prog manual
	for item in WAVEFORM:
		if item > 127:
			RESULT.append((item - 255) * (VOLT_DIV/25) - VOLT_OFFSET)
		else:
			RESULT.append(item * VOLT_DIV/25 - VOLT_OFFSET)
	
	Channel = 3
	VOLT_DIV = device.query(str.format('C%s:Volt_DIV?' % Channel))
	VOLT_DIV = float(VOLT_DIV[len(str.format('C%s:VDIV ' % Channel)):-2])
	
	VOLT_OFFSET = device.query(str.format('C%s:OFfSeT?' % Channel))
	VOLT_OFFSET = float(VOLT_OFFSET[len(str.format('C%s:OFST ' % Channel)):-2])

	# Setup waveform capture
	device.write(str.format('WFSU SP,%d,NP,%d,FP,0' % (Sparsing, Samples)))

	#send capture to controller
	device.write(str.format('C%d:WF? DAT2' % Channel))
	device.chunk_size = 1024*1024*1024

	# read capture from controller
	WAVEFORM1 = device.query_binary_values(str.format('C%d:WF? DAT2' % Channel), datatype='s', is_big_endian=False)
	RESULT1 = []
	#convert raw data to voltage, P142 in prog manual
	for item in WAVEFORM1:
		if item > 127:
			RESULT1.append((item - 255) * (VOLT_DIV/25) - VOLT_OFFSET)
		else:
			RESULT1.append(item * VOLT_DIV/25 - VOLT_OFFSET)
        
	SAMPLE_RATE = device.query('SAMPLE_RATE?')
	SAMPLE_RATE = float(SAMPLE_RATE[len('SARA '):-5])

	TRIG_DELAY = device.query('TRIG_DELAY?')
	TRIG_DELAY = -float(TRIG_DELAY[len('TRDL '):-2])

	#get time interval, P143 in prog manual
	TIME_VALUE = TRIG_DELAY - (TIME_DIV * 14/2)
	TIME_INTERVAL = 1 / SAMPLE_RATE

	#build time axis array
	TIME_AXIS = []
	for i in range(len(RESULT)):
		if i ==0:
			TIME_AXIS.append(TIME_VALUE)
		elif i > 0:
			TIME_AXIS.append(TIME_AXIS[0] + (TIME_INTERVAL * Sparsing)*i)
	TIME_AXIS = np.array(TIME_AXIS)*1000
	oscilloscope_raw_data = np.stack((TIME_AXIS, RESULT, RESULT1), axis=0)
	[idx_start, val] = find_nearest(oscilloscope_raw_data[0], 0)
	[idx_end, val] = find_nearest(oscilloscope_raw_data[0], Time_Scale/1000)
	oscilloscope_trim_data = oscilloscope_raw_data[:,idx_start:idx_end]
	return oscilloscope_trim_data
def parameterMeasureStart():
	#Set Up Voltage Measurement
	
	device.write('PARAMETER_CLR')
	
	device.write(f'PARAMETER_CUSTOM RMS, C{VOLTAGE_CHANNEL}')
	device.write(f'PARAMETER_CUSTOM PKPK, C{VOLTAGE_CHANNEL}')
	device.write(f'PARAMETER_CUSTOM AMPL, C{VOLTAGE_CHANNEL}')
	
	#Set Up Current measurement:
	device.write(f'PARAMETER_CUSTOM RMS, C{CURRENT_CHANNEL}')
	device.write(f'PARAMETER_CUSTOM PKPK, C{CURRENT_CHANNEL}')
	
	
def parameterMeasureRead():
	#Read Voltage
	device.query(f'C{VOLTAGE_CHANNEL}:PARAMETER_VALUE? RMS')
	device.query(f'C{VOLTAGE_CHANNEL}:PARAMETER_VALUE? PKPK')
	
	#Read Current
	device.query(f'C{CURRENT_CHANNEL}:PARAMETER_VALUE? RMS')
	device.query(f'C{CURRENT_CHANNEL}:PARAMETER_VALUE? PKPK')
	
	device.query(f'SAMPLE_NUM? C{VOLTAGE_CHANNEL}')
	device.query(f'SAMPLE_NUM? C{CURRENT_CHANNEL}')
	
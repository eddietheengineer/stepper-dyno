import pyvisa as visa
import numpy as np
import time

try:
    rm = visa.ResourceManager()
    # Connect to device (Make sure to change the resource locator!)
    #device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    device = rm.open_resource('TCPIP::10.10.10.163::INSTR',query_delay=0.25)

except:
    print('Failed to connect to device...')
    sys.exit(0)
device.timeout = 30000
	
def configureScope(Time_Range):
	U_sec = Time_Range / 7
	U_sec_array  = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000]
	[idx, U_sec_set] = find_nearest(U_sec_array, U_sec)
	Trig_delay = -U_sec_set*7
	device.write('TDIV %dUS' % U_sec_set)
	device.write('TRDL %dUS' % Trig_delay)
	return U_sec_set

def find_nearest(array, value):
	array = np.asarray(array)
	idx = (np.abs(array-value)).argmin()
	#if(array[idx] < value):
	#	idx += 1
	return [idx, array[idx]]
	
def captureAll(Sparsing, Samples,Time_Scale):
	#Sparsing = 10000
	#Samples = 10000
	Channel = 1
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
	WAVEFORM = device.query_binary_values(str.format('C%d:WF? DAT2' % Channel), datatype='s', is_big_endian=False)
	RESULT = []
	#convert raw data to voltage, P142 in prog manual
	for item in WAVEFORM:
		if item > 127:
			RESULT.append((item - 255) * (VOLT_DIV/25) - VOLT_OFFSET)
		else:
			RESULT.append(item * VOLT_DIV/25 - VOLT_OFFSET)
	
	Channel = 2
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
        
	SAMPLE_RATE = device.query('SARA?')
	SAMPLE_RATE = float(SAMPLE_RATE[len('SARA '):-5])

	TIME_DIV = device.query('TDIV?')
	TIME_DIV = float(TIME_DIV[len('TDIV '):-2])

	TRIG_DELAY = device.query('TRDL?')
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
	
def param_calc():
	Value = device.query('PACU RMS, C1')
	print(Value)
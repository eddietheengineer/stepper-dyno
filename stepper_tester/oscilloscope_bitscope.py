import numpy as np
from bitlib import *

MY_DEVICE = 0 # one open device only
MY_PROBE_FILE = "" # default probe file if unspecified 
MY_MODE = BL_MODE_FAST # preferred capture mode
MY_SIZE = 12288 # number of samples we'll capture (simply a connectivity test)

BL_Open(MY_PROBE_FILE,1)

def capture(capture_rate):
	print("OS Capture Started")
	BL_Mode(MY_MODE) # prefered capture mode
	BL_Intro(BL_ZERO); # optional, default BL_ZERO
	BL_Delay(BL_ZERO); # optional, default BL_ZERO
	BL_Rate(capture_rate); # optional, default BL_MAX_RATE
	BL_Size(MY_SIZE); # optional default BL_MAX_SIZE
	BL_Select(BL_SELECT_CHANNEL,1); # choose the channel#BL_Trigger(BL_ZERO,BL_TRIG_RISE); # optional when untriggered */
	BL_Select(BL_SELECT_SOURCE,BL_SOURCE_BNC); # use the POD input */
	BL_Range(BL_Count(BL_COUNT_RANGE)); # maximum range
	BL_Offset(BL_ZERO); # optional, default 0
	BL_Enable(1); # at least one channel must be initialised 

	BL_Trace()
	DATA_CURRENT = BL_Acquire()
		
	if (len(DATA_CURRENT) != MY_SIZE):
		DATA_CURRENT = np.concatenate([DATA_CURRENT, np.zeros(MY_SIZE-len(DATA_CURRENT))])

	BL_Mode(MY_MODE) # prefered capture mode
	BL_Intro(BL_ZERO); # optional, default BL_ZERO
	BL_Delay(BL_ZERO); # optional, default BL_ZERO
	BL_Rate(capture_rate); # optional, default BL_MAX_RATE
	BL_Size(MY_SIZE); # optional default BL_MAX_SIZE
	BL_Select(BL_SELECT_CHANNEL,0); # choose the channel#BL_Trigger(BL_ZERO,BL_TRIG_RISE); # optional when untriggered */
	BL_Select(BL_SELECT_SOURCE,BL_SOURCE_BNC); # use the POD input */
	BL_Range(BL_Count(BL_COUNT_RANGE)); # maximum range
	BL_Offset(BL_ZERO); # optional, default 0
	BL_Enable(1); # at least one channel must be initialised 
	
	BL_Trace()
	DATA_VOLTAGE = BL_Acquire()
	
	if (len(DATA_VOLTAGE) != MY_SIZE):
		DATA_VOLTAGE = np.concatenate([DATA_CURRENT, np.zeros(MY_SIZE-len(DATA_CURRENT))])

	y_current = np.array(DATA_CURRENT)
	y_current -= np.mean(y_current, axis=0)
	y_current_max = np.percentile(y_current,95)
	y_current_min = np.percentile(y_current,5)
	y_current_pkpk = (y_current_max - y_current_min)/2
	
	rms_current = np.sqrt(np.mean(y_current**2)) #current
	
	y_voltage = np.array(DATA_VOLTAGE)
	y_voltage_max = np.percentile(y_voltage,95)
	y_voltage_min = np.percentile(y_voltage,5)
	y_voltage_center = (y_voltage_max + y_voltage_min)/2
	y_voltage -= y_voltage_center
	
	rms_voltage = np.sqrt(np.mean(y_voltage**2)) #voltage
	
	rms_watts = rms_current * rms_voltage

	x = np.arange(MY_SIZE)/float(capture_rate)*1000
	
	DATA = np.stack((x, y_voltage, y_current), axis=0)
	
	print(np.shape(DATA))

	return DATA, rms_current, y_current_pkpk, rms_voltage, rms_watts
	print("OS Capture Ended")
	
def close():
	BL_Close()


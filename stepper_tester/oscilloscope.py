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

	#BL_Mode(MY_MODE) # prefered capture mode
	#BL_Intro(BL_ZERO); # optional, default BL_ZERO
	#BL_Delay(BL_ZERO); # optional, default BL_ZERO
	#BL_Rate(capture_rate); # optional, default BL_MAX_RATE
	#BL_Size(MY_SIZE); # optional default BL_MAX_SIZE
	#BL_Select(BL_SELECT_CHANNEL,0); # choose the channel#BL_Trigger(BL_ZERO,BL_TRIG_RISE); # optional when untriggered */
	#BL_Select(BL_SELECT_SOURCE,BL_SOURCE_BNC); # use the POD input */
	#BL_Range(BL_Count(BL_COUNT_RANGE)); # maximum range
	#BL_Offset(BL_ZERO); # optional, default 0
	#BL_Enable(1); # at least one channel must be initialised 
	
	#BL_Trace()
	#DATA_VOLTAGE = BL_Acquire()
	
	print("OS Capture Ended")
	
def close():
	BL_Close()


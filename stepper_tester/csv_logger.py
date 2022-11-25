import os

filepath = '/home/pi/Desktop/%s/' % model_number 
csvfilepath = '/home/pi/Desktop/%s/Data.csv' % model_number

def makedirectory():
	if not os.path.exists(filepath):
		os.makedirs(filepath)
	
def writeheader():
	with open(csvfilepath, "w+") as file:
		if os.stat(csvfilepath).st_size == 0:
			file.write("Setpoint (V),TMC_Current (A),Speed (mm/s),Voltage (V),Current (A),Power_In (W),Stepper_Vrms,Stepper_Arms,Stepper_Apk\n")
	file.close()
	
def writeline():
	with open(csvfilepath, "a") as file:
		file.write("%0.1f,%0.1f,%0.0f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.2f,%0.0f\n" % (r.v_set, tmc_currentx10/10, speed, r.v_out, r.i_out, r.p_out, rms_voltage, rms_current, y_current_pkpk,initial_trace_length))
	file.close()
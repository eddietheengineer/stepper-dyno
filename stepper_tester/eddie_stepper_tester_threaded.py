'''Test the BitScope Library by connecting with the first available device
and performing a capture and dump. Requires BitLib 2.0 and Python Bindings'''

import klipper_serial
import loadcell
import powersupply
import scope_capture
import numpy as np
import time
import terminal_display
import concurrent.futures
import plotting
#import sys
#import csv_logger

model_number = "17HM19-2004S" #str(input('Model Number: ') or "17HS19-2004S1")
step_angle = 0.9
speed_start = 25 #int(input('Start Speed: ') or 50)
speed_end = 1000 #int(input('Ending Speed: ') or 300)
speed_step = 25 #int(input('Speed Step: ') or 50)
tmc_start = 1.0 #float(input('TMC Current Start: ') or 0.5)
tmc_end = 1.0 #float(input('TMC Current End: ') or 1.0)
tmc_step = 0.1 #float(input('TMC Current Step: ') or 0.1)
voltage_start = 48
voltage_end = 48
voltage_step = 12

TIME = 10
ACCELERATION = 20000

powersupply.initialize(voltage_start)
klipper_serial.restart()
loadcell.tare()
time.sleep(1)

initial_time = time.time()
global testcounter
testcounter = 1

#float_formatter = "{:.2f}".format
#np.set_printoptions(formatter={'float_kind':float_formatter})

def main(argv=None):
				
	for voltage_setting in range(voltage_start, voltage_end+voltage_step, voltage_step):
	
		powersupply.voltage_setting(voltage_setting)
		
		for tmc_currentx10 in range (int(tmc_start*10), int(tmc_end*10)+int(tmc_step*10), int(tmc_step*10)):
			tmc_current = tmc_currentx10/10
			klipper_serial.current(tmc_current)

			for speed in range(speed_start, speed_end+speed_step, speed_step):
				global testcounter
				global model_number
				global step_angle
				
				us_per_4fs = round(4*step_angle/(speed/40*365)*1000*1000,0)
				u_sec_set = scope_capture.configureScope(us_per_4fs)
				time.sleep(1)
				
				iterative_data_label = ('test_counter','voltage_setting', 'tmc_current', 'speed')
				iterative_data = (testcounter, voltage_setting, tmc_current, speed)
				start_time = time.time()
				
				klipper_serial.move(TIME, speed, ACCELERATION)

				time.sleep(speed/ACCELERATION+1)
				
				if(u_sec_set == 2000):
					Sparse = np.ceil(us_per_4fs/4000)
				elif(u_sec_set == 5000):
					Sparse = np.ceil(us_per_4fs/10000)
				else:
					Sparse = np.ceil(us_per_4fs/2000)

				with concurrent.futures.ThreadPoolExecutor() as executor:
					f1 = executor.submit(scope_capture.captureAll,Sparse,1000000,us_per_4fs)
					f2 = executor.submit(powersupply.scan)
					f3 = executor.submit(loadcell.singleMeasure)
					
				oscilloscope_raw_data = f1.result()
				
				current_max = np.percentile(oscilloscope_raw_data[2],95)
				current_min = np.percentile(oscilloscope_raw_data[2],5)
				current_pkpk = round((current_max - current_min)/2,2)
				rms_current = round(np.sqrt(np.mean(oscilloscope_raw_data[2]**2)),3)
				rms_voltage = round(np.sqrt(np.mean(oscilloscope_raw_data[1]**2)),2)
				
				oscilloscope_data_label = ('rms_current', 'current_pkpk', 'rms_voltage')
				oscilloscope_data = (rms_current, current_pkpk, rms_voltage)

				grams = f3.result()*-1
				torque = grams / 1000 * 9.81 * 135 / 10
				motor_power = torque / 100 * speed * 2 * 3.1415/40
				
				mech_data_label = ('grams','torque', 'motor_power')
				mech_data = (round(grams,3),round(torque,3), round(motor_power,3))
				
				powersupply_data_label = ('v_set', 'v_out', 'i_out', 'p_out')
				powersupply_data = f2.result()

				if(powersupply_data[2] == 0):
					print('power_supply_error')
				#	powersupply.voltage_setting(voltage_setting)
				#	klipper_serial.restart()
				#	time.sleep(10)
				
				cycle_time = (time.time() - start_time)
				cycle_data_label = ('cycle_time','sparse','samples')
				cycle_data = (round(cycle_time, 2), Sparse, len(oscilloscope_raw_data[0]))

				output_data_label = iterative_data_label + powersupply_data_label + oscilloscope_data_label + mech_data_label+cycle_data_label
				output_data = iterative_data + powersupply_data + oscilloscope_data + mech_data + cycle_data

				terminal_display.display(testcounter, output_data_label, output_data)
				
				plotting.plotData(testcounter, model_number, speed, oscilloscope_raw_data[0],oscilloscope_raw_data[1],oscilloscope_raw_data[2])
				#print("Cycle Time: %0.2f" % cycle_time)
				if cycle_time < TIME:
					time.sleep(TIME - cycle_time)
				#if (grams < 3):
				#	break
				testcounter += 1
				###End Speed Iteration
		
			###End Current Iteration
	final_time = time.time() - initial_time
	powersupply.close()
	klipper_serial.restart()
	loadcell.close()
	print("Finished: Library closed, resources released. Final Time: %0.2f" % final_time)

if __name__ == "__main__":
	import sys
	sys.exit(main())
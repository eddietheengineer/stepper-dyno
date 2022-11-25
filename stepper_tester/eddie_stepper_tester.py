'''Test the BitScope Library by connecting with the first available device
and performing a capture and dump. Requires BitLib 2.0 and Python Bindings'''

import klipper_serial
import loadcell
import powersupply
import scope_capture
import numpy as np
import time
import terminal_display
#import sys
#import csv_logger

model_number = "17HS19-2004S1" #str(input('Model Number: ') or "17HS19-2004S1")
speed_start = 50 #int(input('Start Speed: ') or 50)
speed_end = 300 #int(input('Ending Speed: ') or 300)
speed_step = 50 #int(input('Speed Step: ') or 50)
tmc_start = 1.0 #float(input('TMC Current Start: ') or 0.5)
tmc_end = 1.1 #float(input('TMC Current End: ') or 1.0)
tmc_step = 0.1 #float(input('TMC Current Step: ') or 0.1)
voltage_start = 24
voltage_end = 25
voltage_step = 1

TIME = 3
ACCELERATION = 20000

powersupply.initialize(24)
klipper_serial.restart()
loadcell.tare()
time.sleep(1)

initial_time = time.time()

def main(argv=None):
				
	for voltage_setting in range(voltage_start, voltage_end, voltage_step):
	
		powersupply.voltage_setting(voltage_setting)
		
		for tmc_currentx10 in range (int(tmc_start*10), int(tmc_end*10), int(tmc_step*10)):
			
			klipper_serial.current(tmc_currentx10/10)

			for speed in range(speed_start, speed_end, speed_step):
			
				#MY_RATE = speed * 15360 / 2 #Enough time with 12288 samples to capture two cycles
				#capture_length = MY_SIZE/MY_RATE * 1000 #capture length in ms
				start_time = time.time()
				int_time = start_time
				
				klipper_serial.move(TIME, speed, ACCELERATION)
				print("KlipperSerial %0.2f seconds ---" % (time.time() - int_time))
				int_time = time.time()

				time.sleep(speed/ACCELERATION)
				print("Acceleration %0.2f seconds ---" % (time.time() - int_time))
				int_time = time.time()

				voltage_array = np.array(scope_capture.captureChannel(1,10000,10000))
				current_array = np.array(scope_capture.captureChannel(2,10000,10000))
				time_array = np.array(scope_capture.generateTimeScale(len(voltage_array)))
				oscilloscope_raw_data = np.stack((time_array, voltage_array, current_array), axis=0)

				current_max = np.percentile(oscilloscope_raw_data[2],95)
				current_min = np.percentile(oscilloscope_raw_data[2],5)
				current_pkpk = (current_max - current_min)/2
				rms_current = np.sqrt(np.mean(oscilloscope_raw_data[2]**2))
				rms_voltage = np.sqrt(np.mean(oscilloscope_raw_data[1]**2))

				oscilloscope_data = (rms_current, current_pkpk, rms_voltage)
				print("Oscilloscope %0.2f seconds ---" % (time.time() - int_time))
				int_time = time.time()

				powersupply_data = powersupply.scan()
				print("Power Supply %0.2f seconds ---" % (time.time() - int_time))
				int_time = time.time()

				torque = loadcell.measure(3) / 1000 * 9.81 * 135 / -10
				motor_power = torque / 100 * speed * 2 * 3.1415/40
				mech_data = (torque, motor_power)
				print("Load Cell %0.2f seconds ---" % (time.time() - int_time))
				int_time = time.time()

				#if(powersupply_data[2] == 0):
				#	powersupply.voltage_setting(voltage_setting)
				#	klipper_serial.restart()
				#	time.sleep(10)
				
				output_data = powersupply_data + oscilloscope_data + mech_data
				print("Output %0.2f seconds ---" % (time.time() - int_time))
				int_time = time.time()

				#terminal_display.display(np.concatenate(powersupply_data, torque, motor_power))
				cycle_time = (time.time() - start_time)
				print("Cycle Time: %0.2f" % cycle_time)
				if cycle_time < TIME:
					time.sleep(TIME - cycle_time)
				print("End %0.2f seconds ---\n" % (time.time() - start_time))

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
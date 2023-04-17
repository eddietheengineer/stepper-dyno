import klipper_serial
import loadcell
import powersupply
import scope_capture
import numpy as np
import time
import terminal_display
import concurrent.futures
import plotting
import csv_logger
import sys
import change_config
import csvprocess
import audio_capture

model_number = 'LDO_42STH48-2504AC' #str(input('Model Number: ') or "17HS19-2004S1")
test_id = 'TX2'
step_angle = 1.8

speed_start = 50 #int(input('Start Speed: ') or 50)
speed_end = 3000 #int(input('Ending Speed: ') or 300)
speed_step = 50 #int(input('Speed Step: ') or 50)

tmc_start = 0.6#float(input('TMC Current Start: ') or 0.5)
tmc_end = 2.0 #float(input('TMC Current End: ') or 1.0)
tmc_step = 0.2 #float(input('TMC Current Step: ') or 0.1)
tmc_array_5160 = [0.09, 0.18, 0.26, 0.35, 0.44, 0.53, 0.61, 0.70, 0.79, 0.88, 0.96, 1.14, 1.23, 1.31, 1.40, 1.49, 1.58, 1.66, 1.84, 1.93, 2.01, 2.10, 2.19, 2.28, 2.36, 2.54, 2.63, 2.71, 2.80]

#microstep_array_complete = [1, 2, 4, 8, 16, 32, 64, 128]
microstep_array = [16]

voltage_start = 12
voltage_end = 48
voltage_step = 12

ACCELERATION = 10000
SAMPLE_TARGET = 500000

global TIME_MOVE
TIME_MOVE = 10
initial_time = time.time()
global testcounter
testcounter = 1
global failcount
failcount = 0
global cycle_time
cycle_time = 0


def main(argv=None):
	
	initialize_dyno(voltage_start)
				
	for voltage_setting in range(voltage_start, voltage_end+voltage_step, voltage_step):
		
		#Set Power Supply Voltage
		powersupply.voltage_setting(voltage_setting)
				
		for microstep_i in range(len(microstep_array)):
			
			#Set Microsteps
			change_config.updateMS(microstep_array[microstep_i])
			klipper_serial.restart()
			time.sleep(10)
		
			for tmc_currentx10 in range (int(tmc_start*10), int(tmc_end*10)+int(tmc_step*10), int(tmc_step*10)):
				
				#Set TMC Driver Current
				tmc_current = find_closest(tmc_array_5160, tmc_currentx10/10)
				klipper_serial.current(tmc_current)
			
				for speed in range(speed_start, speed_end+speed_step, speed_step):
					
					global TIME_MOVE
					global testcounter
					global failcount
					global cycle_time
				
					#If previous move was longer than cycle time, delay until move is completed
					if (cycle_time < TIME_MOVE)and(testcounter>1):
						time_delay = TIME_MOVE - cycle_time
						time.sleep(time_delay+1)
				
					#Set new move to the same as the previous move, plus a small buffer of 0.5 sec
					if (testcounter>1):
						TIME_MOVE = 10 #np.ceil(cycle_time)+1
								
					#Initiate Capture Timer
					start_time = time.time()
				
					#Calculate length of 1 Cycle
					Cycle_Length_us = round(4*step_angle/(speed/40*365)*1000*1000,0)
				
					#Start Stepper Motor
					klipper_serial.move(TIME_MOVE, speed, ACCELERATION)
				
					#Write Summary Array
					iterative_data_label = ('model_number','test_id','test_counter','voltage_setting', 'microstep','tmc_current', 'speed')
					iterative_data = (model_number, test_id, testcounter, voltage_setting, microstep_array[microstep_i], tmc_current, speed)
				
					#Wait for Stepper to accelerate
					time.sleep(speed/ACCELERATION)
					
					#time.sleep(1)
					#audio_capture.captureAudio(iterative_data)
					#time.sleep(1)
				
					#Start threads for measurement devices
					with concurrent.futures.ThreadPoolExecutor() as executor:
						f3 = executor.submit(loadcell.measure,7)
						f2 = executor.submit(powersupply.scan)
						f1 = executor.submit(scope_capture.captureAllSingle,SAMPLE_TARGET,Cycle_Length_us,voltage_setting,tmc_current)
						#f4 = executor.submit(audio_capture.captureAudio,iterative_data)
						#f5 = executor.submit(klipper_serial.readtemp)

					#Process Oscilloscope Data
					oscilloscope_raw_data = f1.result()
					current_max = np.percentile(oscilloscope_raw_data[2],95)
					current_min = np.percentile(oscilloscope_raw_data[2],5)
					current_pkpk = round((current_max - current_min)/2,2)
					rms_current = round(np.sqrt(np.mean(oscilloscope_raw_data[2]**2)),3)
					rms_voltage = round(np.sqrt(np.mean(oscilloscope_raw_data[1]**2)),2)
					oscilloscope_data_label = ('rms_current', 'current_pkpk', 'rms_voltage')
					oscilloscope_data = (rms_current, current_pkpk, rms_voltage)

					#Process Load Cell Data
					grams = f3.result()
					torque = grams / 1000 * 9.81 * 135 / 10
					motor_power = torque / 100 * speed * 2 * 3.1415/40
					mech_data_label = ('grams','torque', 'motor_power')
					mech_data = (round(grams,3),round(torque,3), round(motor_power,3))
				
					#Process Power Supply Data
					powersupply_data_label = ('v_set', 'v_supply', 'i_supply', 'p_supply')
					#powersupply_data2 = powersupply.scan()
					powersupply_data = f2.result()
				
					#Process Cycle Data
					cycle_time = (time.time() - start_time)
					cycle_data_label = ('cycle_time','TIME_MOVE','samples')
					cycle_data = (round(cycle_time, 2), TIME_MOVE,len(oscilloscope_raw_data[0]))
				
					#Process Temperature
					temperature_label = ('rpi_temp','driver_temp','stepper_temp')
					temperature_data = klipper_serial.readtemp()

					#Combine Output Summary Data
					output_data_label = iterative_data_label + powersupply_data_label + oscilloscope_data_label + mech_data_label+cycle_data_label + temperature_label
					output_data = iterative_data + powersupply_data + oscilloscope_data + mech_data + cycle_data + temperature_data

					#Write Header File Data to CSV File
					if (testcounter == 1):
						csv_logger.writeheader(model_number, test_id, output_data_label)
				
					#Check if motor has stalled
					if (grams < 5)and(speed>500):
						failcount += 1
						print('Failcount: %s, Grams: %0.1f, Speed: %d' % (failcount, grams, speed))
				
					if (failcount > 2):
						#If motor has stalled twice, exit for loop
						failcount = 0
						break
					else:
						#Plot Oscilloscope Data if motor hasn't stalled
						plotting.plotosData(output_data, oscilloscope_raw_data[0],oscilloscope_raw_data[1],oscilloscope_raw_data[2])
					
						#Write to CSV File
						csv_logger.writedata(model_number, test_id, output_data)
					
						#Write Output Data to Terminal
						terminal_display.display(testcounter, output_data_label, output_data)
					
						#Write Output Data to Array
						#full_array = np.append(full_array, output_data, axis=0)
						#print(full_array)

					###End Speed Iteration
					testcounter += 1

			
				###End Current Iteration

	csvprocess.plotSummaryData(model_number)
	shutdown_dyno()


def initialize_dyno(voltage):
	powersupply.initialize(voltage_start)
	klipper_serial.restart()
	time.sleep(1)
	loadcell.tare()
	
def shutdown_dyno():
	powersupply.close()
	klipper_serial.restart()
	loadcell.close()
	print("Finished: Library closed, resources released")


def find_closest(array, target):
    return min(array, key=lambda x: abs(x - target))

if __name__ == "__main__":
	import sys
	sys.exit(main())
	

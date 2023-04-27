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
from dataclasses import dataclass

# str(input('Model Number: ') or "17HS19-2004S1")
model_number = 'LDO_42STH48-2504AC'
test_id = '4.27.23'
step_angle = 1.8

speed_start = 25  # int(input('Start Speed: ') or 50)
speed_end = 3000  # int(input('Ending Speed: ') or 300)
speed_step = 25  # int(input('Speed Step: ') or 50)

tmc_start = 0.6  # float(input('TMC Current Start: ') or 0.5)
tmc_end = 2.4  # float(input('TMC Current End: ') or 1.0)
tmc_step = 0.2  # float(input('TMC Current Step: ') or 0.1)
# tmc_array_5160_small = [0.09, 0.18, 0.26, 0.35, 0.44, 0.53, 0.61, 0.70, 0.79, 0.88, 0.96, 1.14, 1.23, 1.31, 1.40, 1.49, 1.58, 1.66, 1.84, 1.93, 2.01, 2.10, 2.19, 2.28, 2.36, 2.54, 2.63, 2.71, 2.80]
tmc_array_5160 = [0.08, 0.16, 0.23, 0.31, 0.39, 0.47, 0.63, 0.70, 0.78, 0.86, 0.94, 1.02, 1.09, 1.17, 1.25,
                  1.33, 1.49, 1.56, 1.64, 1.72, 1.80, 1.88, 1.96, 2.03, 2.11, 2.19, 2.27, 2.35, 2.42, 2.54, 2.63, 2.71, 2.8]

# microstep_array_complete = [1, 2, 4, 8, 16, 32, 64, 128]
microstep_array = [16]

voltage_start = 12
voltage_end = 48
voltage_step = 12

global reset_counter
reset_counter = 1

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


@dataclass
class TestPointData():
    stepper_model: str
    test_id: str
    test_counter: int
    test_voltage: int
    test_microstep: int
    test_current: float
    test_speed: int
    powersupplyvoltage: float
    powersupplycurrent_a: float
    powersupplypower_w: float
    oscilloscopecurrentrms_a: float
    oscilloscopecurrentpeak_a: float
    oscilloscopevoltagerms_v: float
    oscilloscopepower_w: float
    oscilloscopesamplecount: int
    loadcellload_g: float
    loadcelltorque_ncm: float
    loadcellmotoroutputpower_w: float
    temperaturepi_c: float
    temperaturedriver_c: float
    temperaturestepper_c: float
    cycletime_s: float
    movetime_s: float


def main():

    # Start and connect to all devices
    initialize_dyno(voltage_start)

    for voltage_setting in range(voltage_start, voltage_end+voltage_step, voltage_step):

        # Set Power Supply Voltage
        powersupply.voltage_setting(voltage_setting)

        for microstep_i in range(len(microstep_array)):

            # Update Microstep configuration, then restart Klipper to accept change
            change_config.updateMS(microstep_array[microstep_i])
            klipper_serial.restart()
            print('Starting Sleep Time - 20 seconds')
            time.sleep(20)

            for tmc_currentx10 in range(int(tmc_start*10), int(tmc_end*10)+int(tmc_step*10), int(tmc_step*10)):

                # Set TMC Driver Current
                tmc_current = find_closest(tmc_array_5160, tmc_currentx10/10)
                klipper_serial.current(tmc_current)
                scope_capture.configureScopeVerticalAxis(
                    voltage_setting, tmc_current)
                speed = speed_start
                while (speed <= speed_end):

                    global TIME_MOVE
                    global testcounter
                    global failcount
                    global cycle_time
                    global reset_counter

                    # If previous move was longer than cycle time, delay until move is completed
                    if (cycle_time < TIME_MOVE) and (testcounter > 1):
                        time_delay = TIME_MOVE - cycle_time
                        time.sleep(time_delay+1)

                    # Set new move to the same as the previous move, plus a small buffer of 0.5 sec
                    if (testcounter > 1):
                        TIME_MOVE = 10  # np.ceil(cycle_time)+1

                    # Initiate Capture Timer
                    start_time = time.perf_counter()

                    # Calculate length of 1 Cycle
                    Cycle_Length_us = round(
                        4*step_angle/(speed/40*360)*1000*1000, 0)

                    # Start Stepper Motor
                    klipper_serial.move(TIME_MOVE, speed, ACCELERATION)

                    # Write Summary Array
                    iterative_data_label = ('model_number', 'test_id', 'test_counter',
                                            'voltage_setting', 'microstep', 'tmc_current', 'speed', 'reset_counter')
                    iterative_data = (model_number, test_id, testcounter, voltage_setting,
                                      microstep_array[microstep_i], tmc_current, speed, reset_counter)

                    # Wait for Stepper to accelerate
                    time.sleep(speed/ACCELERATION+0.5)

                    # Start threads for measurement devices
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        f3 = executor.submit(loadcell.measure, 7)
                        f2 = executor.submit(powersupply.measure, 10)
                        # f1 = executor.submit(scope_capture.captureAllSingle,SAMPLE_TARGET,Cycle_Length_us)
                        # f4 = executor.submit(audio_capture.captureAudio,iterative_data)
                        # f5 = executor.submit(klipper_serial.readtemp)

                    # Process Load Cell Data
                    [grams, loadcell_time, lc_samples] = f3.result()
                    if grams < 0:
                        grams = 0
                    torque = grams / 1000 * 9.81 * 135 / 10
                    motor_power = torque / 100 * speed * 2 * 3.1415/40
                    mech_data_label = ('grams', 'torque',
                                       'motor_power', 'lc_samples')
                    mech_data = (round(grams, 3), round(torque, 3),
                                 round(motor_power, 3), lc_samples)

                    # Process Power Supply Data
                    [voltage_actual, power_actual,
                        powersupply_time, samples] = f2.result()
                    powersupply_data_label = (
                        'v_supply', 'p_supply', 'p_samples')
                    powersupply_data = (voltage_actual, power_actual, samples)

                    # Process Oscilloscope Data
                    # [oscilloscope_raw_data, os_time] = f1.result()
                    [oscilloscope_raw_data, os_time, error_count, error_delta, orig_len,
                        sparsing] = scope_capture.captureAllSingle(SAMPLE_TARGET, Cycle_Length_us)
                    if ((error_count == 0) & (error_delta == 0)):
                        current_max = np.percentile(
                            oscilloscope_raw_data[2], 95)
                        current_min = np.percentile(
                            oscilloscope_raw_data[2], 5)
                        current_pkpk = round((current_max - current_min)/2, 2)

                        current_rms = round(
                            np.sqrt(np.mean(oscilloscope_raw_data[2]**2)), 3)
                        voltage_rms = round(
                            np.sqrt(np.mean(oscilloscope_raw_data[1]**2)), 2)

                        power_raw = np.multiply(
                            oscilloscope_raw_data[1], oscilloscope_raw_data[2])
                        power_max = round(np.percentile(power_raw, 90), 2)
                        power_average = round(np.average(power_raw)*2, 2)

                        oscilloscope_data_label = (
                            'voltage_rms', 'current_rms', 'current_pkpk', 'power_average', 'power_max', 'errors', 'error_delta')
                        oscilloscope_data = (
                            voltage_rms, current_rms, current_pkpk, power_average, power_max, error_count, error_delta)

                        # Process Temperature
                        temperature_label = (
                            'rpi_temp', 'driver_temp', 'stepper_temp')
                        temperature_data = klipper_serial.readtemp()

                        # Process Cycle Data
                        cycle_time = (time.perf_counter() - start_time)
                        cycle_data_label = (
                            'cycle_time', 'TIME_MOVE', 'orig_len', 'samples', 'sparsing')
                        cycle_data = (round(cycle_time, 2), TIME_MOVE, orig_len, len(
                            oscilloscope_raw_data[0]), sparsing)

                        # Combine Output Summary Data
                        output_data_label = iterative_data_label + powersupply_data_label + \
                            oscilloscope_data_label + mech_data_label+cycle_data_label + temperature_label
                        output_data = iterative_data + powersupply_data + \
                            oscilloscope_data + mech_data + cycle_data + temperature_data

                        # Write Header File Data to CSV File
                        if (testcounter == 1):
                            csv_logger.writeheader(
                                model_number, test_id, output_data_label)

                        # Check if motor has stalled
                        if (grams < 5) and (speed > 500):
                            failcount += 1
                            print('Failcount: %s, Grams: %0.1f, Speed: %d' %
                                  (failcount, grams, speed))

                        if (failcount > 2):
                            # If motor has stalled twice, exit for loop
                            failcount = 0
                            break
                        else:
                            # Write to CSV File
                            csv_logger.writedata(
                                model_number, test_id, output_data)

                            # Write Output Data to Terminal
                            terminal_display.display(
                                testcounter, output_data_label, output_data)

                            if (failcount == 0):
                                # Plot Oscilloscope Data if motor hasn't stalled
                                plot_time = plotting.plotosData(
                                    output_data, output_data_label, oscilloscope_raw_data[0], oscilloscope_raw_data[1], oscilloscope_raw_data[2], power_raw)
                                # print(f'      Total: {cycle_time:0.2f}, PS: {powersupply_time:0.2f}, Load: {loadcell_time:0.2f}, OS: {os_time:0.2f}, PlotTime: {plot_time:0.2f}')

                        # End Speed Iteration
                        speed += speed_step
                        testcounter += 1

                    else:
                        print(
                            f'Reset Cycle: Error Count = {error_count}, Error Delta = {error_delta}')
                        klipper_serial.restart()
                        time.sleep(15)
                        klipper_serial.current(tmc_current)
                        cycle_time = (time.perf_counter() - start_time)
                        reset_counter += 1

             # End Current Iteration

    # csvprocess.plotSummaryData(model_number)
    shutdown_dyno()


def initialize_dyno(voltage):
    powersupply.initialize(voltage)
    klipper_serial.restart()
    time.sleep(1)
    loadcell.tare
    scope_capture.setupScope()

def shutdown_dyno():
    powersupply.close()
    klipper_serial.restart()
    loadcell.close()
    print("Finished: Library closed, resources released")

def find_closest(array, target):
    return min(array, key=lambda x: abs(x - target))

if __name__ == "__main__":
    sys.exit(main())
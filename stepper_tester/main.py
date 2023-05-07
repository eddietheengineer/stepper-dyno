import klipper_serial
import loadcell
import powersupply
import scope_capture
import time
import terminal_display
import concurrent.futures
import csv_logger
import sys

import change_config
# import plotting
from dataclasses import dataclass, fields

model_number = 'LDO_42STH48-2504AC'
test_id = '5.7.23a'
step_angle = 1.8
motor_resistance = 1.5
iron_constant = 0.01

speed_start = 10  # int(input('Start Speed: ') or 50)
speed_end = 3000  # int(input('Ending Speed: ') or 300)
speed_step = 10  # int(input('Speed Step: ') or 50)

tmc_start = 1.0  # float(input('TMC Current Start: ') or 0.5)
tmc_end = 2.0  # float(input('TMC Current End: ') or 1.0)
tmc_step = 0.5  # float(input('TMC Current Step: ') or 0.1)
# tmc_array_5160_small = [0.09, 0.18, 0.26, 0.35, 0.44, 0.53, 0.61, 0.70, 0.79, 0.88, 0.96, 1.14, 1.23, 1.31, 1.40, 1.49, 1.58, 1.66, 1.84, 1.93, 2.01, 2.10, 2.19, 2.28, 2.36, 2.54, 2.63, 2.71, 2.80]
tmc_array_5160 = [0.08, 0.16, 0.23, 0.31, 0.39, 0.47, 0.63, 0.70, 0.78, 0.86, 0.94, 1.02, 1.09, 1.17, 1.25,
                  1.33, 1.49, 1.56, 1.64, 1.72, 1.80, 1.88, 1.96, 2.03, 2.11, 2.19, 2.27, 2.35, 2.42, 2.54, 2.63, 2.71, 2.8]

# microstep_array_complete = [1, 2, 4, 8, 16, 32, 64, 128]
microstep_array = [16,128]
voltage_array = [24, 48]

reset_counter = 1

ACCELERATION = 10000
SAMPLE_TARGET = 500100

TIME_MOVE = 10
CYCLES_MEASURED = 1
NO_LOAD_TEST = False
testcounter = 1
failcount = 0
cycle_time = 0


@dataclass
class TestIdData():
    stepper_model: str = model_number
    test_id: str = test_id
    test_counter: int = 0
    test_voltage: int = 0
    test_microstep: int = 0
    test_current: float = 0
    test_speed: int = 0
    test_resetcounter: int = 0

@dataclass
class AllData():
    id: TestIdData
    mech: loadcell.loadcelldata
    psu: powersupply.powersupplydata
    scope: scope_capture.oscilloscopedata
    temps: klipper_serial.temperaturedata

@dataclass
class PowerSummary():
    driverpower_in = float
    driverpower_out = float
    driverpower_loss = float
    motorpower_totalloss = float
    motorpower_copperloss = float
    motorpower_ironloss = float
    motorpower_miscerror = float
    motorpower_output = float


def main():

    # Start and connect to all devices
    initialize_dyno(voltage_array[0])

    for _, voltage_setting in enumerate(voltage_array):

        # Set Power Supply Voltage
        powersupply.voltage_setting(voltage_setting)

        for _, microstep in enumerate(microstep_array):

            # Update Microstep configuration, then restart Klipper to accept change
            change_config.updateMS(microstep)
            klipper_serial.restart()
            print('      Starting Sleep Time - 15 seconds')
            time.sleep(15)

            for tmc_currentx10 in range(int(tmc_start*10), int(tmc_end*10)+int(tmc_step*10), int(tmc_step*10)):

                # Set TMC Driver Current
                tmc_current = find_closest(tmc_array_5160, tmc_currentx10/10)
                klipper_serial.current(tmc_current)
                scope_capture.configureScopeVerticalAxis(
                    voltage_setting, tmc_current)
                previous_peak_current = tmc_current
                speed = speed_start

                while (speed <= speed_end):

                    global TIME_MOVE
                    global testcounter
                    global failcount
                    global cycle_time
                    global reset_counter

                    testid = TestIdData(test_counter=testcounter,
                                        test_voltage=voltage_setting,
                                        test_microstep=microstep,
                                        test_current=tmc_current,
                                        test_speed=speed)
                    
                    # Write Summary Array
                    testid_label = tuple(field.name for field in fields(testid))
                    testid_data = tuple(testid.__dict__.values())

                    # If previous peak current was < tmc_current*1.4, change to
                    if (previous_peak_current < tmc_current * 1.4 * .5) & (previous_peak_current > 0.1):
                        scope_capture.configureScopeVerticalAxis(
                            voltage_setting, previous_peak_current/1.414)

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
                        4*step_angle/(speed/40*360)*1000*1000 * CYCLES_MEASURED, 0)

                    # Start Stepper Motor
                    klipper_serial.move(TIME_MOVE, speed, ACCELERATION)

                    # Wait for Stepper to accelerate
                    time.sleep(speed/ACCELERATION+0.5)

                    # Start threads for measurement devices
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        f3 = executor.submit(loadcell.measure, 10, speed)
                        f2 = executor.submit(powersupply.measure, 10)
                        f1 = executor.submit(
                            scope_capture.captureAllSingle, SAMPLE_TARGET, Cycle_Length_us)
                        # f4 = executor.submit(klipper_serial.readtemp)
                        # f5 = executor.submit(audio_capture.captureAudio, iterative_data, iterative_data_label,)

                    # Process Load Cell Data
                    mech = f3.result()
                    mech_label = tuple(field.name for field in fields(mech))
                    mech_data = tuple(mech.__dict__.values())

                    # Process Power Supply Data
                    psu = f2.result()
                    psu_label = tuple(field.name for field in fields(psu))
                    psu_data = tuple(psu.__dict__.values())

                    # Process Oscilloscope Data
                    scope, scoperaw = f1.result()
                    scope_label = tuple(field.name for field in fields(scope))
                    scope_data = tuple(scope.__dict__.values())

                    # Process Temperature
                    temps = klipper_serial.readtemp()
                    temp_label = tuple(field.name for field in fields(temps))
                    temp_data = tuple(temps.__dict__.values())

                    testcompletedata = AllData(id=testid, mech= mech, psu=psu, scope=scope, temps=temps)
                    
                    header, data = convertData(testcompletedata)

                    # Check if oscilloscope actually captured data
                    if ((scope.errorcounts == 0) & (scope.errorpct < 5)):

                        # Check if motor has stalled
                        if (mech.grams < 5) and (speed > 500) and (NO_LOAD_TEST is False):
                            failcount += 1
                            print(f'Failcount: {failcount}, Speed: {speed}')

                        if (failcount > 2):
                            # If motor has stalled twice, exit for loop
                            failcount = 0
                            break

                        if (failcount == 0):
                            # Plot Oscilloscope Data if motor hasn't stalled
                            #plotting.plotosData(output_data, output_data_label, oscilloscopedata.oscilloscope_time_array, oscilloscopedata.oscilloscope_voltage_array,
                            #                    oscilloscopedata.oscilloscope_current_array, oscilloscopedata.oscilloscope_power_array)
                            csv_logger.writeoscilloscopedata(testid, scoperaw)

                        # Process Cycle Data
                        cycle_time = (time.perf_counter() - start_time)
                        cycle_data_label = ('cycle_time', 'TIME_MOVE')
                        cycle_data = (round(cycle_time, 2), TIME_MOVE)

                        # Combine Output Summary Data
                        output_data_label = testid_label + psu_label + \
                            scope_label + mech_label + \
                            cycle_data_label + temp_label
                        output_data = testid_data + psu_data + \
                            scope_data + mech_data + \
                            cycle_data + temp_data

                        # Write Header File Data to CSV File
                        if (testcounter == 1):
                            csv_logger.writeheader(
                                model_number, test_id, output_data_label)

                        # Write to CSV File
                        csv_logger.writedata(
                            model_number, test_id, output_data)

                        # Write Output Data to Terminal
                        #terminal_display.display(
                        #    testcounter, output_data_label, output_data)
                        terminal_display.display(testcounter, header, data)

                        # End Speed Iteration
                        speed += speed_step
                        previous_peak_current = scope.ampout_pk
                        testcounter += 1

                    else:
                        print(
                            f'Reset Cycle: Error Count = {scope.errorcounts}, Error % = {scope.errorpct}')
                        klipper_serial.restart()
                        time.sleep(15)
                        klipper_serial.current(tmc_current)
                        cycle_time = (time.perf_counter() - start_time)
                        reset_counter += 1
                # End Speed Iteration

            # End Current Iteration

        # End Microstep Iteration

    # End Voltage Iteration

    # csvprocess.plotSummaryData(model_number)
    shutdown_dyno()


def initialize_dyno(voltage):
    powersupply.initialize(voltage)
    klipper_serial.restart()
    time.sleep(1)
    loadcell.tare()
    scope_capture.setupScope()


def shutdown_dyno():
    powersupply.close()
    klipper_serial.restart()
    loadcell.close()
    print("Finished: Library closed, resources released")


def find_closest(array, target):
    return min(array, key=lambda x: abs(x - target))


def calculatepower(testdata, loadcell, powersupply, oscilloscope):
    output = PowerSummary()
    output.motorpower_output = loadcell.motorpower

    output.driverpower_in = powersupply.measuredpower
    output.driverpower_out = oscilloscope.power_av
    output.driverpower_loss = output.driverpower_in - \
        output.driverpower_out

    output.motorpower_totalloss = output.driverpower_out - \
        output.motorpower_output
    output.motorpower_copperloss = 2 * \
        oscilloscope.current_av**2 * motor_resistance
    output.motorpower_ironloss = testdata.speed * \
        oscilloscope.current_pk * iron_constant
    output.motorpower_miscerror = output.motorpower_totalloss - \
        output.motorpower_copperloss - output.motorpower_ironloss

def convertData(data):
    flat_dict = {}
    header_file = []
    data_file = []
    for k, v in data.__dict__.items():
        for k2, v2 in v.__dict__.items():
            new_key = f'{k}.{k2}'
            flat_dict[new_key] = v2
            header_file.append(new_key)
            data_file.append(flat_dict[new_key])
    return header_file, data_file

if __name__ == "__main__":

    sys.exit(main())

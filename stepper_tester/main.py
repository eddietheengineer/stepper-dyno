import klipper_serial
import loadcell
import powersupply
import scope_capture
import time
import terminal_display
import concurrent.futures
import csvlogger
import sys
import csvprocess
import audiocapture

import change_config
import plotting
from dataclasses import dataclass

model_number = 'LDO_42STH48-2504AC'
test_id = '5.7.23p2'
step_angle = 1.8
motor_resistance = 1.5
iron_constant = 0.01

speed_start = 10  # int(input('Start Speed: ') or 50)
speed_end = 3000  # int(input('Ending Speed: ') or 300)
speed_step = 10  # int(input('Speed Step: ') or 50)

tmc_start = 0.62  # float(input('TMC Current Start: ') or 0.5)
tmc_end = 1.8  # float(input('TMC Current End: ') or 1.0)
tmc_step = 0.16  # float(input('TMC Current Step: ') or 0.1)
# tmc_array_5160_small = [0.09, 0.18, 0.26, 0.35, 0.44, 0.53, 0.61, 0.70, 0.79, 0.88, 0.96, 1.14, 1.23,
#                        1.31, 1.40, 1.49, 1.58, 1.66, 1.84, 1.93, 2.01, 2.10, 2.19, 2.28, 2.36, 2.54, 2.63, 2.71, 2.80]
tmc_array_5160 = [0.08, 0.16, 0.23, 0.31, 0.39, 0.47, 0.63, 0.70, 0.78, 0.86, 0.94, 1.02, 1.09, 1.17, 1.25,
                  1.33, 1.4, 1.49, 1.56, 1.64, 1.72, 1.80, 1.88, 1.96, 2.03, 2.11, 2.19, 2.27, 2.35, 2.42, 2.54, 2.63, 2.71, 2.8]

# microstep_array_complete = [1, 2, 4, 8, 16, 32, 64, 128]
microstep_array = [16]
voltage_array = [48]

reset_counter = 1

ACCELERATION = 10000
SAMPLE_TARGET = 500100

TIME_MOVE = 15
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
    test_steppertime: float = 0
    test_cycletime: float = 0


@dataclass
class PowerSummary():
    driverpower_in: float = 0
    driverpower_out: float = 0
    driverpower_loss: float = 0
    motorpower_totalloss: float = 0
    motorpower_copperloss: float = 0
    motorpower_ironloss: float = 0
    motorpower_miscerror: float = 0
    motorpower_output: float = 0
    failcount: int = 0


@dataclass
class AllData():
    id: TestIdData
    mech: loadcell.loadcelldata
    psu: powersupply.powersupplydata
    scope: scope_capture.oscilloscopedata
    temps: klipper_serial.temperaturedata
    powersummary: PowerSummary


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

            for tmc_currentx100 in range(int(tmc_start*100), int(tmc_end*100)+int(tmc_step*100), int(tmc_step*100)):

                # Find closest valid setting
                tmc_current = find_closest(tmc_array_5160, tmc_currentx100/100)
                # Set current via Klipper
                klipper_serial.current(tmc_current)
                # Set Oscilloscope scales for new current
                scope_capture.configureScopeVerticalAxis(
                    voltage_setting, tmc_current)
                # Initialize scaling variable to capture reduced current
                previous_peak_current = tmc_current*1.414
                # Set Speed Value to the start value
                speed = speed_start

                while (speed <= speed_end):

                    global TIME_MOVE
                    global testcounter
                    global failcount
                    global cycle_time
                    global reset_counter

                    # Initialize Test identification dataClass
                    testid = TestIdData(test_counter=testcounter,
                                        test_voltage=voltage_setting,
                                        test_microstep=microstep,
                                        test_current=tmc_current,
                                        test_speed=speed)

                    # If previous peak current was < 50% of tmc_current*1.4, zoom in
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
                        4*step_angle/(speed/40*360)*1000*1000, 0)

                    # Start Stepper Motor
                    klipper_serial.move(TIME_MOVE, speed, ACCELERATION)

                    # Wait for Stepper to accelerate
                    time.sleep(speed/ACCELERATION+0.5)

                    # Start threads for measurement devices
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        # Capture 10 samples from loadcell
                        f3 = executor.submit(loadcell.measure, 10, speed)
                        # Capture readings (1V, 1A, 10W) from powersupply
                        f2 = executor.submit(powersupply.measure, 10)
                        # Initialize capture of X full cycles from Oscilloscope
                        f1 = executor.submit(
                            scope_capture.captureAllSingle, SAMPLE_TARGET, Cycle_Length_us * CYCLES_MEASURED)
                        f4 = executor.submit(audiocapture.recordAudio, testid, 5)
                        # f5 = executor.submit(audio_capture.captureAudio, iterative_data, iterative_data_label,)

                    # Record Oscilloscope Data
                    scope, scoperaw = f1.result()

                    powercalc = PowerSummary()

                    # Combine all measured data
                    alldata = AllData(id=testid, mech=f3.result(), psu=f2.result(
                    ), scope=scope, temps=klipper_serial.readtemp(), powersummary=powercalc)

                    # Check if oscilloscope actually captured data
                    if ((alldata.scope.errorcounts == 0) & (alldata.scope.errorpct < 5) & (alldata.mech.samples > 3)):

                        # Check if motor has stalled
                        if (alldata.mech.grams < 5) and (alldata.id.test_speed > 500) and (NO_LOAD_TEST is False):
                            failcount += 1
                            print(
                                f'Failcount: {failcount}, Speed: {alldata.id.test_speed}')

                        alldata.powersummary = calculatepower(alldata,failcount)

                        if (failcount == 0):
                            # Plot Oscilloscope Data if motor hasn't stalled
                            plotting.plotosData(alldata, scoperaw, type='In')
                            plotting.plotosData(alldata, scoperaw, type='Out')
                            csvlogger.writeoscilloscopedata(
                                alldata.id, scoperaw)

                        elif (failcount > 2):
                            # If motor has stalled twice, exit for loop
                            failcount = 0
                            break

                        # Calculate Cycle Time
                        cycle_time = round(time.perf_counter() - start_time, 1)
                        alldata.id.test_cycletime = cycle_time
                        alldata.id.test_steppertime = TIME_MOVE

                        # Create flattened data for CSV/Terminal
                        header, data = convertData(alldata)

                        # Write Header File Data to CSV File
                        if (testcounter == 1):
                            csvlogger.writeheader(
                                alldata.id.stepper_model, alldata.id.test_id, header)

                        # Write to CSV File
                        csvlogger.writedata(
                            alldata.id.stepper_model, alldata.id.test_id, data)

                        # Write Output Data to Terminal
                        # terminal_display.display(
                        #    testcounter, output_data_label, output_data)
                        terminal_display.display(
                            alldata.id.test_counter, header, data)

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

    csvprocess.generateplots(model_number,test_id)
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


def calculatepower(alldata, failcount):
    output = PowerSummary()
    output.failcount = failcount
    output.motorpower_output = alldata.mech.motorpower

    output.driverpower_in = alldata.psu.measuredpower
    output.driverpower_out = alldata.scope.powerout_av
    output.driverpower_loss = round(output.driverpower_in -
                                    output.driverpower_out, 2)

    output.motorpower_totalloss = round(output.driverpower_out -
                                        output.motorpower_output, 2)
    output.motorpower_copperloss = round(2 *
                                         alldata.scope.ampout_av**2 * motor_resistance, 2)
    if (failcount > 0):
        output.motorpower_ironloss = round(alldata.id.test_speed *
                                       alldata.scope.ampout_pk * iron_constant, 2)
        output.motorpower_miscerror = round(output.motorpower_totalloss -
                                        output.motorpower_copperloss - output.motorpower_ironloss, 2)
    return output


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

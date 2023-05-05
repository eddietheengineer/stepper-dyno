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
import plotting
from dataclasses import dataclass, fields

# str(input('Model Number: ') or "17HS19-2004S1")
model_number = 'LDO_42STH48-2504AC'
test_id = '5.5.2023a'
step_angle = 1.8
motor_resistance = 1.5
iron_constant = 0.01

speed_start = 10  # int(input('Start Speed: ') or 50)
speed_end = 3000  # int(input('Ending Speed: ') or 300)
speed_step = 10  # int(input('Speed Step: ') or 50)

tmc_start = 1.8  # float(input('TMC Current Start: ') or 0.5)
tmc_end = 1.8  # float(input('TMC Current End: ') or 1.0)
tmc_step = 0.8  # float(input('TMC Current Step: ') or 0.1)
# tmc_array_5160_small = [0.09, 0.18, 0.26, 0.35, 0.44, 0.53, 0.61, 0.70, 0.79, 0.88, 0.96, 1.14, 1.23, 1.31, 1.40, 1.49, 1.58, 1.66, 1.84, 1.93, 2.01, 2.10, 2.19, 2.28, 2.36, 2.54, 2.63, 2.71, 2.80]
tmc_array_5160 = [0.08, 0.16, 0.23, 0.31, 0.39, 0.47, 0.63, 0.70, 0.78, 0.86, 0.94, 1.02, 1.09, 1.17, 1.25,
                  1.33, 1.49, 1.56, 1.64, 1.72, 1.80, 1.88, 1.96, 2.03, 2.11, 2.19, 2.27, 2.35, 2.42, 2.54, 2.63, 2.71, 2.8]

# microstep_array_complete = [1, 2, 4, 8, 16, 32, 64, 128]
microstep_array = [16]

voltage_start = 48
voltage_end = 48
voltage_step = 36

reset_counter = 1

ACCELERATION = 10000
SAMPLE_TARGET = 501000

TIME_MOVE = 10
CYCLES_MEASURED = 2
NO_LOAD_TEST = False
testcounter = 1
failcount = 0
cycle_time = 0


@dataclass
class TestIdData():
    stepper_model: str
    test_id: str
    test_counter: int
    test_voltage: int
    test_microstep: int
    test_current: float
    test_speed: int


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


@dataclass
class IterativeData():
    voltage_setting: int
    microstep_setting: int
    current_setting: float
    speed_setting: int

def main():

    # Start and connect to all devices
    initialize_dyno(voltage_start)

    for voltage_setting in range(voltage_start, voltage_end+voltage_step, voltage_step):

        # Set Power Supply Voltage
        powersupply.voltage_setting(voltage_setting)

        for _, microstep in enumerate(microstep_array):

            # Update Microstep configuration, then restart Klipper to accept change
            change_config.updateMS(microstep)
            klipper_serial.restart()
            print('      Starting Sleep Time - 10 seconds')
            time.sleep(10)

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

                    # If previous peak current was < tmc_current*1.4, change to
                    if (previous_peak_current < tmc_current * 1.4 * .5):
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

                    # Write Summary Array
                    iterative_data_label = ('model_number', 'test_id', 'test_counter',
                                            'voltage_setting', 'microstep', 'tmc_current', 'speed', 'reset_counter')
                    iterative_data = (model_number, test_id, testcounter, voltage_setting,
                                      microstep, tmc_current, speed, reset_counter)

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
                    loadcelldata = f3.result()

                    mech_data_label = tuple(field.name for field in fields(loadcelldata))
                    mech_data = (round(loadcelldata.grams, 3), round(loadcelldata.torque, 3), round(
                        loadcelldata.motorpower, 3), loadcelldata.samples)

                    # Process Power Supply Data
                    powersupplydata = f2.result()
                    powersupply_data_label = tuple(field.name for field in fields(powersupplydata))
                    powersupply_data = (
                        powersupplydata.measuredvoltage, powersupplydata.measuredpower)

                    # Process Oscilloscope Data
                    oscilloscopedata, oscilloscoperawdata = f1.result()
                    #oscilloscope_data_label1 = tuple(field.name for field in fields(oscilloscopedata))[4:]
                    oscilloscope_data_label = (
                        'voltage_rms', 'current_pkpk', 'current_rms',  'current_average', 'power_average', 'power_max')
                    oscilloscope_data = (oscilloscopedata.voltage_rms, oscilloscopedata.current_pk, oscilloscopedata.current_rms, oscilloscopedata.current_av, oscilloscopedata.power_av, oscilloscopedata.power_pk)

                    oscilloscope_reference_label = (
                        'sparsing', 'orig_samples', 'trim_samples', 'error_delta', 'errors')
                    oscilloscope_reference_data = (oscilloscopedata.sparsing, oscilloscopedata.capturerawlength,
                                                   oscilloscopedata.capturetrimlength, oscilloscopedata.errortime, oscilloscopedata.errorcounts)

                    # Process Temperature
                    temperaturedata = klipper_serial.readtemp()
                    temperature_label = (
                        'rpi_temp', 'driver_temp', 'stepper_temp')
                    temperature_data = (
                        temperaturedata.rpitemp, temperaturedata.drivertemp, temperaturedata.steppertemp)

                    # Check if oscilloscope actually captured data
                    if ((oscilloscopedata.errorcounts == 0) & (round(oscilloscopedata.errortime,1) < 5)):

                        # Check if motor has stalled
                        if (loadcelldata.grams < 5) and (speed > 500) and (NO_LOAD_TEST is False):
                            failcount += 1
                            print(f'Failcount: {failcount}, Speed: {speed}')

                        if (failcount > 2):
                            # If motor has stalled twice, exit for loop
                            failcount = 0
                            break

                        # if (failcount == 0):
                        #     # Plot Oscilloscope Data if motor hasn't stalled
                        #     plotting.plotosData(output_data, output_data_label, oscilloscopedata.oscilloscope_time_array, oscilloscopedata.oscilloscope_voltage_array,
                        #                         oscilloscopedata.oscilloscope_current_array, oscilloscopedata.oscilloscope_power_array)
                        #     csv_logger.writeoscilloscopedata(output_data, output_data_label, np.stack(
                        #         oscilloscopedata.oscilloscope_time_array,
                        #         oscilloscopedata.oscilloscope_voltage_array,
                        #         oscilloscopedata.oscilloscope_current_array,
                        #         oscilloscopedata.oscilloscope_power_array), axis=0)

                        # Process Cycle Data
                        cycle_time = (time.perf_counter() - start_time)
                        cycle_data_label = ('cycle_time', 'TIME_MOVE')
                        cycle_data = (round(cycle_time, 2), TIME_MOVE)

                        # Combine Output Summary Data
                        output_data_label = iterative_data_label + powersupply_data_label + \
                            oscilloscope_data_label + oscilloscope_reference_label + \
                            mech_data_label+cycle_data_label + temperature_label
                        output_data = iterative_data + powersupply_data + \
                            oscilloscope_data + oscilloscope_reference_data + \
                            mech_data + cycle_data + temperature_data

                        # Write Header File Data to CSV File
                        if (testcounter == 1):
                            csv_logger.writeheader(
                                model_number, test_id, output_data_label)

                        # Write to CSV File
                        csv_logger.writedata(
                            model_number, test_id, output_data)

                        # Write Output Data to Terminal
                        terminal_display.display(
                            testcounter, output_data_label, output_data)

                        # End Speed Iteration
                        speed += speed_step
                        previous_peak_current = oscilloscopedata.current_pk
                        testcounter += 1

                    else:
                        print(
                            f'Reset Cycle: Error Count = {oscilloscopedata.errorcounts}, Error Delta = {oscilloscopedata.errortime}')
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
    PowerSummary.motorpower_output = loadcell.motorpower

    PowerSummary.driverpower_in = powersupply.measuredpower
    PowerSummary.driverpower_out = oscilloscope.power_av
    PowerSummary.driverpower_loss = PowerSummary.driverpower_in - PowerSummary.driverpower_out

    PowerSummary.motorpower_totalloss = PowerSummary.driverpower_out - PowerSummary.motorpower_output
    PowerSummary.motorpower_copperloss = 2 * oscilloscope.current_av**2 * motor_resistance
    PowerSummary.motorpower_ironloss = testdata.speed * oscilloscope.current_pk * iron_constant
    PowerSummary.motorpower_miscerror = PowerSummary.motorpower_totalloss - PowerSummary.motorpower_copperloss - PowerSummary.motorpower_ironloss

if __name__ == "__main__":

    sys.exit(main())
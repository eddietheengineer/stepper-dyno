import pyvisa as visa
import numpy as np
import math as math
import time
import sys
import re

TOTAL_CHANNELS = 4
CURRENT_CHANNEL = 3
VOLTAGE_CHANNEL = 1

# Oscilloscope Settings:
global TIME_DIV
TIME_DIV = 0
global TRIG_DELAY
TRIG_DELAY = 0
global VOLT_DIV
VOLT_DIV = 0
global AMP_DIV
AMP_DIV = 0
global VOLT_OFFSET
VOLT_OFFSET = 0
global AMP_OFFSET
AMP_OFFSET = 0
global SHARED_CHANNELS
SHARED_CHANNELS = 0

try:
    rm = visa.ResourceManager()
    # Connect to device (Make sure to change the resource locator!)
    # device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    # device = rm.open_resource('TCPIP::10.10.10.163::INSTR',query_delay=0.25)
    device = rm.open_resource('TCPIP::192.168.1.128::INSTR', query_delay=0.25)

except:
    print('      Failed to connect to oscilloscope')
    sys.exit(0)
device.timeout = 30000


def startChannels():
    global SHARED_CHANNELS
    channelStatus = [-1, -1, -1, -1]
    for i in range(1, TOTAL_CHANNELS+1):
        if ((i == CURRENT_CHANNEL) | (i == VOLTAGE_CHANNEL)):
            device.write(f'C{i}:TRACE ON')
            # print(f'{i} is ON')
            channelStatus[i-1] = 1
        else:
            device.write(f'C{i}:TRACE OFF')
            # print(f'{i} is OFF')
            channelStatus[i-1] = 0

        if ((channelStatus[0] == 1 & channelStatus[1] == 1) | (channelStatus[2] == 1 & channelStatus[3] == 1)):
            SHARED_CHANNELS = 2  # warning this doesn't make sense
        else:
            SHARED_CHANNELS = 1  # warning this doesn't make sense


def setupScope():
    print('      Connected to Oscilloscope')
    startChannels()

    # use sampling instead of average
    device.write('ACQUIRE_WAY SAMPLING')

    # Set Trigger Mode
    device.write(f'TRIG_MODE NORM')
    # Set Trigger Level to 0V
    device.write(f'C{CURRENT_CHANNEL}:TRIG_LEVEL 100mV')
    # Set Trigger Coupling to AC
    device.write(f'C{CURRENT_CHANNEL}:TRIG_COUPLING DC')
    # Set Trigger Select to EDGE and Current Channel
    device.write(f'TRIG_SELECT EDGE, SR, C{CURRENT_CHANNEL}')
    # Set Trigger Slope Positive
    device.write(f'C{CURRENT_CHANNEL}:TRIG_SLOPE POS')

    # set memory depth to 14M Samples
    device.write('MEMORY_SIZE 14M')
    # Turn Off Persistent Display
    device.write('PERSIST OFF')

    # Set Voltage Channel to Volts
    device.write(f'C{VOLTAGE_CHANNEL}:UNIT V')
    # Set Voltage Channel to 10X
    device.write(f'C{VOLTAGE_CHANNEL}:ATTENUATION 10')
    # Set Voltage Channel to DC Coupling
    device.write(f'C{VOLTAGE_CHANNEL}:COUPLING D1M')
    # Set Voltage Channel Vertical Offset to 0
    device.write(f'C{VOLTAGE_CHANNEL}:OFFSET {VOLT_OFFSET}V')

    # Set Current Channel to Amps
    device.write(f'C{CURRENT_CHANNEL}:UNIT A')
    # Set Current Channel to 10X
    device.write(f'C{CURRENT_CHANNEL}:ATTENUATION 10')
    # Set Current Channel to DC Coupling
    device.write(f'C{CURRENT_CHANNEL}:COUPLING D1M')
    # Set Current Channel Vertical Offset to 0V
    device.write(f'C{CURRENT_CHANNEL}:OFFSET {AMP_OFFSET}V')

    # Set Buzzer Off
    device.write('BUZZER OFF')


def configureScopeHorizontalAxis(CaptureTime_us):
    global TIME_DIV
    global TRIG_DELAY
    # Supported Configurations for Siglent SDS1104
    TimePerDivisionOptions_us = [1, 2, 5, 10, 20, 50, 100,
                                 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]

    # Display is 14 sections wide, add 10% buffer
    TimePerDivisionRaw_us = CaptureTime_us / 14

    # Find closest option available to raw value
    [x, TimePerDivision_us] = findFirstInstanceGreaterThan(TimePerDivisionOptions_us, TimePerDivisionRaw_us)

    # Set Trigger Delay so T=0 is on left of screen
    TriggerDelay_us = -TimePerDivision_us*7
    # Write configuration parameters to Oscilloscope if changed
    if (TimePerDivision_us != TIME_DIV):
        device.write(f'TIME_DIV {TimePerDivision_us}US')
        device.write(f'TRIG_DELAY {TriggerDelay_us}US')
        TIME_DIV = TimePerDivision_us
        TRIG_DELAY = TriggerDelay_us
    return TimePerDivision_us


def configureScopeVerticalAxis(inputVoltage, targetCurrentRms):
    global VOLT_DIV
    global AMP_DIV

    # Volts -> mV -> 4 sections -> 200% of data
    VoltsPerDivision_V = math.ceil(inputVoltage/4*2)
    if (VoltsPerDivision_V != VOLT_DIV):
        device.write(f'C{VOLTAGE_CHANNEL}:VOLT_DIV {VoltsPerDivision_V}V')
        print(f'      Updated VOLT DIV Old:{VOLT_DIV}, New:{VoltsPerDivision_V}')
        VOLT_DIV = VoltsPerDivision_V

    # Amps -> A -> 4 sections -> Arms to Apkpk -> 150% of data
    AmpsPerDivision_A = math.ceil(targetCurrentRms*10/4*1.4*1.5)/10
    if (AmpsPerDivision_A != AMP_DIV):
        device.write(f'C{CURRENT_CHANNEL}:VOLT_DIV {AmpsPerDivision_A*1000}mV')
        print(f'      Updated AMP DIV Old:{AMP_DIV}, New:{AmpsPerDivision_A}')
        AMP_DIV = AmpsPerDivision_A


def findFirstInstanceGreaterThan(array, value):
    for x in range(len(array)):
        if array[x] > value:
            return [x, array[x]]


def findClosestValue(array, value):
    array = np.asarray(array)
    idx = (np.abs(array-value)).argmin()
    return [idx, array[idx]]


def captureAllSingle(Samples, Time_Scale):
    global VOLT_DIV
    global VOLT_OFFSET

    global AMP_DIV
    global AMP_OFFSET

    global TIME_DIV
    global TRIG_DELAY

    global SHARED_CHANNELS

    start_time = time.perf_counter()

    u_sec_set = configureScopeHorizontalAxis(Time_Scale)

    SHARED_CHANNELS = 1
    if (u_sec_set == 5000):
        # At 5000 samples, we have 17.5M samples per screen instead of just 14
        Sparsing = np.ceil(Time_Scale*17.5/14/(Samples/200))*SHARED_CHANNELS
    elif (u_sec_set == 2000):
        Sparsing = np.ceil(Time_Scale/(Samples/500))*SHARED_CHANNELS
    else:
        Sparsing = np.ceil(Time_Scale/(Samples/1000))*SHARED_CHANNELS

    # Setup waveform capture
    device.write(str.format(f'WAVEFORM_SETUP SP,{Sparsing},NP,{Samples},FP,0'))
    # Start Capture
    device.write('ARM')
    device.write('WAIT')
    time.sleep(0.5)

    ################# Capture Data #################
    VOLTAGE_WAVEFORM = []
    CURRENT_WAVEFORM = []
    error_counts = 0
    orig_length = 0
    while ((len(VOLTAGE_WAVEFORM) == 0) & (error_counts == 0)):
        [VOLTAGE_WAVEFORM, CURRENT_WAVEFORM] = collectOscilloscopeData()
        if (len(VOLTAGE_WAVEFORM) == 0):
            print(
                f'Missed Data: Error - {error_counts}, Length - {len(VOLTAGE_WAVEFORM)}')
            error_counts += 1

    if (len(VOLTAGE_WAVEFORM) != 0):
        ################# VOLTAGE PROCESS #################
        VOLTAGE_RESULT = []
        # convert raw data to voltage, P142 in prog manual
        for item in VOLTAGE_WAVEFORM:
            if item > 127:
                VOLTAGE_RESULT.append(
                    (item - 255) * (VOLT_DIV/25) - VOLT_OFFSET)
            else:
                VOLTAGE_RESULT.append(item * VOLT_DIV/25 - VOLT_OFFSET)
        orig_length = len(VOLTAGE_RESULT)

        ################# CURRENT PROCESS #################
        CURRENT_RESULT = []
        # convert raw data to voltage, P142 in prog manual
        for item in CURRENT_WAVEFORM:
            if item > 127:
                CURRENT_RESULT.append((item - 255) * (AMP_DIV/25) - AMP_OFFSET)
            else:
                CURRENT_RESULT.append(item * AMP_DIV/25 - AMP_OFFSET)

        ################# TIME PROCESS #################
        SAMPLE_RATE = device.query('SAMPLE_RATE?')
        SAMPLE_RATE = float(SAMPLE_RATE[len('SARA '):-5])
        Time_Interval_ms = 1 / SAMPLE_RATE * 1000

        # get time interval, P143 in prog manual
        Initial_Time_Value = TRIG_DELAY + (TIME_DIV * 14/2)

        # build time axis array
        TIME_AXIS = []
        for i in range(len(VOLTAGE_RESULT)):
            if i == 0:
                TIME_AXIS.append(Initial_Time_Value)
            elif i > 0:
                TIME_AXIS.append(
                    TIME_AXIS[0] + (Time_Interval_ms * Sparsing)*i)
        TIME_AXIS = np.array(TIME_AXIS)

        # Combine data into one array
        oscilloscope_raw_data = np.stack(
            (TIME_AXIS, VOLTAGE_RESULT, CURRENT_RESULT), axis=0)

        # Trim to length of one cycle
        [idx_start, val] = findClosestValue(oscilloscope_raw_data[0], 0)
        [idx_end, val] = findClosestValue(
            oscilloscope_raw_data[0], (Initial_Time_Value + Time_Scale/1000))
        oscilloscope_trim_data = oscilloscope_raw_data[:, idx_start:idx_end]
        delta = round(Time_Scale/1000 - oscilloscope_trim_data[0, -1], 1)
        os_time = time.perf_counter() - start_time
        return [oscilloscope_trim_data, os_time, error_counts, delta, orig_length, Sparsing]
    else:
        return [0, 0, error_counts, 1, orig_length, Sparsing]


def collectOscilloscopeData():
    # send capture to controller
    device.write(str.format(f'C{CURRENT_CHANNEL}:WAVEFORM? DAT2'))
    device.write(str.format(f'C{VOLTAGE_CHANNEL}:WAVEFORM? DAT2'))
    device.chunk_size = 1024*1024*1024

    # read capture from controller
    VOLTAGE_WAVEFORM = device.query_binary_values(str.format(
        f'C{VOLTAGE_CHANNEL}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
    CURRENT_WAVEFORM = device.query_binary_values(str.format(
        f'C{CURRENT_CHANNEL}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)
    return VOLTAGE_WAVEFORM, CURRENT_WAVEFORM


def parseOscilloscopeResponse(response):
    match = re.search(r'([-+]?\d*\.\d+([eE][-+]?\d+)?)', response)

    if match:
        processedResponse = float(match.group(1))
    else:
        processedResponse = None
    return processedResponse


def parameterMeasureStart():
    # Set Up Voltage Measurement
    device.write('PARAMETER_CLR')

    device.write(f'PARAMETER_CUSTOM RMS, C{VOLTAGE_CHANNEL}')
    device.write(f'PARAMETER_CUSTOM PKPK, C{VOLTAGE_CHANNEL}')

    # Set Up Current measurement:
    device.write(f'PARAMETER_CUSTOM RMS, C{CURRENT_CHANNEL}')
    device.write(f'PARAMETER_CUSTOM PKPK, C{CURRENT_CHANNEL}')

    # Set Up Math Measurement
    device.write("'DEFINE_EQN, 'C1*C3'")


def parameterMeasureRead():
    # Read Voltage
    volt_rms = parseOscilloscopeResponse(device.query(
        f'C{VOLTAGE_CHANNEL}:PARAMETER_VALUE? RMS'))
    volt_pk = parseOscilloscopeResponse(device.query(
        f'C{VOLTAGE_CHANNEL}:PARAMETER_VALUE? PKPK'))

    # Read Current
    current_rms = parseOscilloscopeResponse(
        device.query(f'C{CURRENT_CHANNEL}:PARAMETER_VALUE? RMS'))
    current_pk = parseOscilloscopeResponse(
        device.query(f'C{CURRENT_CHANNEL}:PARAMETER_VALUE? PKPK'))
    return round(volt_rms, 1), round(volt_pk, 1), round(current_rms, 3), round(current_pk, 3)
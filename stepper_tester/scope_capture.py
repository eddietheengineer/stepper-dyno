import pyvisa as visa
import numpy as np
import math
import time
import sys
import re
from dataclasses import dataclass

TOTAL_CHANNELS = 4
CURRENT_CHANNEL = 2
VOLTAGE_CHANNEL = 1
INPUT_VOLTAGE_CHANNEL = 3
INPUT_CURRENT_CHANNEL = 4

# Oscilloscope Settings:
TIME_DIV = 0
TRIG_DELAY = 0
VOLT_DIV = 0
AMP_DIV = 0
INPUT_VOLT_DIV = 0
INPUT_AMP_DIV = 0
SAMPLE_RATE = 0
VOLT_OFFSET = 0
AMP_OFFSET = 0
INPUT_VOLT_OFFSET = 0
INPUT_AMP_OFFSET = 0
SHARED_CHANNELS = 0


@dataclass
class oscilloscopedata:
    capturetime: float = 0
    errorcounts: int = 0
    errortime: float = 0
    capturerawlength: int = 0
    capturetrimlength: int = 0
    sparsing: int = 0
    current_av: float = 0
    current_rms: float = 0
    current_pk: float = 0
    voltage_av: float = 0
    voltage_rms: float = 0
    voltage_pk: float = 0
    power_av: float = 0
    power_rms: float = 0
    power_pk: float = 0


@dataclass
class oscilloscoperawdata:
    time_array: np.ndarray = np.array([])
    voltage_array: np.ndarray = np.array([])
    current_array: np.ndarray = np.array([])
    power_array: np.ndarray = np.array([])


try:
    rm = visa.ResourceManager()
    # Connect to device (Make sure to change the resource locator!)
    # device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    device = rm.open_resource('TCPIP::192.168.1.128::INSTR', query_delay=0.25)

except Exception:
    print('      Failed to connect to oscilloscope')
    sys.exit(0)
device.timeout = 5000


def startChannels():
    global SHARED_CHANNELS
    channelStatus = [-1, -1, -1, -1]
    for i in range(1, TOTAL_CHANNELS+1):
        if ((i == CURRENT_CHANNEL) | (i == VOLTAGE_CHANNEL) | (i==INPUT_VOLTAGE_CHANNEL) | (i==INPUT_CURRENT_CHANNEL)):
            device.write(f'C{i}:TRACE ON')
            # print(f'{i} is ON')
            channelStatus[i-1] = 1
        else:
            device.write(f'C{i}:TRACE OFF')
            # print(f'{i} is OFF')
            channelStatus[i-1] = 0

        if ((channelStatus[0] == 1 & channelStatus[1] == 1) | (channelStatus[2] == 1 & channelStatus[3] == 1)):
            SHARED_CHANNELS = 2
        else:
            SHARED_CHANNELS = 1


def setupScope():
    print('      Connected to Oscilloscope')
    startChannels()

    # use sampling instead of average
    device.write('ACQUIRE_WAY SAMPLING')

    # Set Trigger Mode
    device.write('TRIG_MODE NORMAL')
    # Set Trigger Level to 0V
    device.write(f'C{CURRENT_CHANNEL}:TRIG_LEVEL 100mV')
    # Set Trigger Coupling to AC
    device.write(f'C{CURRENT_CHANNEL}:TRIG_COUPLING DC')
    # Set Trigger Select to EDGE and Current Channel
    device.write(f'TRIG_SELECT EDGE, SR, C{CURRENT_CHANNEL}')
    # Set Trigger Slope Positive
    device.write(f'C{CURRENT_CHANNEL}:TRIG_SLOPE POS')

    # set memory depth to 14M Samples
    # device.write('MEMORY_SIZE 14M')
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

    # Set Voltage Channel to Volts
    device.write(f'C{INPUT_VOLTAGE_CHANNEL}:UNIT V')
    # Set Voltage Channel to 10X
    device.write(f'C{INPUT_VOLTAGE_CHANNEL}:ATTENUATION 10')
    # Set Voltage Channel to DC Coupling
    device.write(f'C{INPUT_VOLTAGE_CHANNEL}:COUPLING D1M')
    # Set Voltage Channel Vertical Offset to 0
    device.write(f'C{INPUT_VOLTAGE_CHANNEL}:OFFSET {INPUT_VOLT_OFFSET}V')

    # Set Current Channel to Amps
    device.write(f'C{INPUT_CURRENT_CHANNEL}:UNIT A')
    # Set Current Channel to 10X
    device.write(f'C{INPUT_CURRENT_CHANNEL}:ATTENUATION 10')
    # Set Current Channel to DC Coupling
    device.write(f'C{INPUT_CURRENT_CHANNEL}:COUPLING D1M')
    # Set Current Channel Vertical Offset to 0V
    device.write(f'C{INPUT_CURRENT_CHANNEL}:OFFSET {INPUT_AMP_OFFSET}V')

    # Set Buzzer Off
    device.write('BUZZER OFF')


def configureScopeHorizontalAxis(CaptureTime_us):
    global TIME_DIV
    global TRIG_DELAY
    # Supported Configurations for Siglent SDS1104
    TimePerDivisionOptions_us = [1, 2, 5, 10, 20, 50, 100,
                                 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]

    # Display is 14 sections wide
    TimePerDivisionRaw_us = CaptureTime_us / 14

    # Find closest option available to raw value
    [_, TimePerDivision_us] = findFirstInstanceGreaterThan(
        TimePerDivisionOptions_us, TimePerDivisionRaw_us)

    # Set Trigger Delay so T=0 is on left of screen
    TriggerDelay_us = -TimePerDivision_us*7
    # Write configuration parameters to Oscilloscope if changed
    if (TimePerDivision_us != TIME_DIV):
        device.write(f'TIME_DIV {TimePerDivision_us}US')
        device.write(f'TRIG_DELAY {TriggerDelay_us}US')
        TIME_DIV = TimePerDivision_us
        TRIG_DELAY = TriggerDelay_us


def configureScopeVerticalAxis(inputVoltage, targetCurrentRms):
    global VOLT_DIV
    global AMP_DIV
    global INPUT_VOLT_DIV
    global INPUT_AMP_DIV

    # Output Volts -> mV -> 4 sections -> 200% of data
    VoltsPerDivision_V = math.ceil(inputVoltage/4*2)
    if (VoltsPerDivision_V != VOLT_DIV):
        device.write(f'C{VOLTAGE_CHANNEL}:VOLT_DIV {VoltsPerDivision_V}V')
        print(f'VOLT DIV Old:{VOLT_DIV}, New:{VoltsPerDivision_V}')
        VOLT_DIV = VoltsPerDivision_V

    # Output Amps -> A -> 4 sections -> Arms to Apkpk -> 150% of data
    AmpsPerDivision_A = math.ceil(targetCurrentRms*10/4*1.4*1.5)/10
    if (AmpsPerDivision_A != AMP_DIV):
        device.write(f'C{CURRENT_CHANNEL}:VOLT_DIV {AmpsPerDivision_A*1000}mV')
        print(f'AMP DIV Old:{AMP_DIV}, New:{AmpsPerDivision_A}')
        AMP_DIV = AmpsPerDivision_A

    #INPUT_VOLTS
    #Set Offset Equal to Input Voltage so trace is centered in display
    VoltsOffset_inV = -int(inputVoltage)
    #Set Scaling so that the display shows +/-50% of input voltage
    VoltsPerDivision_inV = math.ceil(inputVoltage/2/4)

    if (VoltsPerDivision_inV != INPUT_VOLT_DIV) | (VoltsOffset_inV != INPUT_VOLT_OFFSET):
        device.write(f'C{INPUT_VOLT_OFFSET}:OFFSET {VoltsOffset_inV}V')
        device.write(f'C{INPUT_VOLTAGE_CHANNEL}:VOLT_DIV {VoltsPerDivision_inV}V')
        print(f'IN VOLT OFFSET Old:{INPUT_VOLT_OFFSET}, New:{VoltsOffset_inV}')
        print(f'IN VOLT DIV Old:{INPUT_VOLT_DIV}, New:{VoltsPerDivision_inV}')
        INPUT_VOLT_OFFSET = VoltsOffset_inV
        INPUT_VOLT_DIV = VoltsPerDivision_inV

    # Input Amps -> A -> 4 sections -> Arms to Apkpk -> 150% of data
    AmpsPerDivision_inA = math.ceil(targetCurrentRms*10/4*1.4*1.5)/10
    if (AmpsPerDivision_inA != INPUT_AMP_DIV):
        device.write(f'C{INPUT_CURRENT_CHANNEL}:VOLT_DIV {AmpsPerDivision_inA*1000}mV')
        print(f'IN AMP DIV Old:{INPUT_AMP_DIV}, New:{AmpsPerDivision_inA}')
        INPUT_AMP_DIV = AmpsPerDivision_inA




def findFirstInstanceGreaterThan(array, value):
    output = [0, 0]
    for x, arrayvalue in enumerate(array):
        if arrayvalue > value:
            output = [x, arrayvalue]
            break
    return output


def findClosestValue(array, value):
    array = np.asarray(array)
    idx = (np.abs(array-value)).argmin()
    return [idx, array[idx]]


def setSparsing(Samples, Time_Scale):
    if (TIME_DIV == 20000):
        Sparsing = int(np.ceil(Time_Scale/(Samples/50)/SHARED_CHANNELS))
    elif (TIME_DIV == 10000):
        Sparsing = int(np.ceil(Time_Scale/(Samples/100)/SHARED_CHANNELS))
    elif (TIME_DIV == 5000):
        # At 5ms/div, we have 17.5M samples per screen instead of just 14
        Sparsing = int(np.ceil(Time_Scale*17.5/14 /
                       (Samples/200)/SHARED_CHANNELS))
    elif (TIME_DIV == 2000):
        Sparsing = int(np.ceil(Time_Scale/(Samples/500)/SHARED_CHANNELS))
    else:
        Sparsing = int(np.ceil(Time_Scale/(Samples/1000)/SHARED_CHANNELS))

    return Sparsing


def captureAllSingle(Samples, Time_Scale):
    start_time = time.perf_counter()

    configureScopeHorizontalAxis(Time_Scale)
    Sparsing = setSparsing(Samples, Time_Scale)

    # Setup waveform capture
    device.write(str.format(f'WAVEFORM_SETUP SP,{Sparsing},NP,{Samples},FP,0'))
    # Start Capture
    time.sleep(1)
    device.write('ARM')
    device.write('WAIT')
    time.sleep(1)

    ################# Capture Data #################
    VOLTAGE_WAVEFORM = []
    CURRENT_WAVEFORM = []
    error_counts = 0

    while ((len(VOLTAGE_WAVEFORM) == 0) & (error_counts == 0)):
        [VOLTAGE_WAVEFORM, CURRENT_WAVEFORM] = collectOscilloscopeData()
        if (len(VOLTAGE_WAVEFORM) == 0):
            print(
                f'Missed Data: Error - {error_counts}, Length - {len(VOLTAGE_WAVEFORM)}')
            error_counts += 1

    output = oscilloscopedata()

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

        # Trim to length of one cycle
        [idx_start, _] = findClosestValue(TIME_AXIS, 0)
        [idx_end, _] = findClosestValue(
            TIME_AXIS, (Initial_Time_Value + Time_Scale/1000))

        TIME_AXIS = np.array(TIME_AXIS[idx_start:idx_end])
        VOLTAGE_RESULT = np.array(VOLTAGE_RESULT[idx_start:idx_end])
        CURRENT_RESULT = np.array(CURRENT_RESULT[idx_start:idx_end])
        POWER_RESULT = np.multiply(VOLTAGE_RESULT, CURRENT_RESULT)[
            idx_start:idx_end]

        output_raw = oscilloscoperawdata(
            time_array=TIME_AXIS, voltage_array=VOLTAGE_RESULT, 
            current_array=CURRENT_RESULT, power_array=POWER_RESULT)

        output.capturerawlength = len(VOLTAGE_WAVEFORM)
        output.capturetrimlength = len(output_raw.voltage_array)
        output.errortime = abs(round((Time_Scale/1000 - output_raw.time_array[-1])/(Time_Scale/1000)*100, 2))

        output.current_pk = round(float(np.percentile(output_raw.current_array, 95)), 2)
        output.current_rms = round(np.sqrt(np.mean(np.square(output_raw.current_array))), 3)
        output.current_av = round(float(np.average(np.absolute(output_raw.current_array))), 3)

        output.voltage_pk = round(float(np.percentile(output_raw.voltage_array, 95)), 2)
        output.voltage_rms = round(np.sqrt(np.mean(np.square(output_raw.voltage_array))), 2)
        output.voltage_av = round(float(np.average(np.absolute(output_raw.voltage_array))), 3)

        output.power_pk = round(float(np.percentile(output_raw.power_array, 95)), 2)
        output.power_rms = round(np.sqrt(np.mean(np.square(output_raw.power_array))), 3)
        output.power_av = round(float(np.average(output_raw.power_array)*2), 2)

        output.capturetime = round(time.perf_counter() - start_time, 2)

    else:
        output_raw = oscilloscoperawdata()

    output.sparsing = Sparsing
    output.errorcounts = error_counts

    return output, output_raw


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
    time.sleep(1)
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
    return volt_rms, volt_pk, current_rms, current_pk

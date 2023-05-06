import pyvisa as visa
import numpy as np
import math
import time
import sys
import re
from dataclasses import dataclass

TOTAL_CHANNELS = 4
VOLTAGE_CHANNEL = 1
CURRENT_CHANNEL = 2
INPUT_VOLTAGE_CHANNEL = 3
INPUT_CURRENT_CHANNEL = 4

CHANNEL_LIST = ['VOLTAGE_CHANNEL', 'CURRENT_CHANNEL',
                'INPUT_VOLTAGE_CHANNEL', 'INPUT_CURRENT_CHANNEL']

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
INPUT_AMP_OFFSET = -1
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


def initializeChannels(Channel_Definition):
    for i, val in enumerate(Channel_Definition):
        if (val == 0):
            device.write(f'C{i+1}:TRACE OFF')
        else:
            device.write(f'C{i+1}:TRACE ON')


def findSharedChannels(Channel_Definition):
    global SHARED_CHANNELS
    if (((Channel_Definition[0] != 0) & (Channel_Definition[1] != 0)) |
       ((Channel_Definition[2] != 0) & (Channel_Definition[3] != 0))):
        SHARED_CHANNELS = 2
    else:
        SHARED_CHANNELS = 1


def setTrigger(Channel, LevelmV):
    # Set Trigger Mode
    device.write('TRIG_MODE NORMAL')
    # Set Trigger Level to 0V
    device.write(f'C{Channel}:TRIG_LEVEL {LevelmV}mV')
    # Set Trigger Coupling to AC
    device.write(f'C{Channel}:TRIG_COUPLING DC')
    # Set Trigger Select to EDGE and Current Channel
    device.write(f'TRIG_SELECT EDGE, SR, C{Channel}')
    # Set Trigger Slope Positive
    device.write(f'C{Channel}:TRIG_SLOPE POS')


def configureChannel(Channel, Attenuation, OffsetV, Unit):
    # Set Voltage Channel to Volts
    device.write(f'C{Channel}:UNIT {Unit}')
    # Set Voltage Channel to 10X
    device.write(f'C{Channel}:ATTENUATION {Attenuation}')
    # Set Voltage Channel to DC Coupling
    device.write(f'C{Channel}:COUPLING D1M')
    # Set Voltage Channel Vertical Offset to 0
    device.write(f'C{Channel}:OFFSET {OffsetV}V')


def setupScope():
    print('      Connected to Oscilloscope')
    initializeChannels(CHANNEL_LIST)
    findSharedChannels(CHANNEL_LIST)

    # use sampling instead of average
    device.write('ACQUIRE_WAY SAMPLING')

    # set memory depth to 14M Samples
    # device.write('MEMORY_SIZE 14M')

    # Turn Off Persistent Display
    device.write('PERSIST OFF')

    # Set Buzzer Off
    device.write('BUZZER OFF')

    setTrigger(CURRENT_CHANNEL, 100)
    configureChannel(VOLTAGE_CHANNEL, 10, VOLT_OFFSET, 'V')
    configureChannel(CURRENT_CHANNEL, 10, AMP_OFFSET, 'A')
    configureChannel(INPUT_VOLTAGE_CHANNEL, 10, INPUT_VOLT_OFFSET, 'V')
    configureChannel(INPUT_CURRENT_CHANNEL, 10, INPUT_AMP_OFFSET, 'A')


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
    global INPUT_VOLT_OFFSET

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

    # INPUT_VOLTS
    # Set Scaling so that the display shows +/-50% of input voltage
    VoltsPerDivision_inV = math.ceil(inputVoltage*.20 / 8)

    # Set Offset Equal to Input Voltage so trace is centered in display
    VoltsOffset_inV = -inputVoltage + VoltsPerDivision_inV

    if (VoltsPerDivision_inV != INPUT_VOLT_DIV) | (VoltsOffset_inV != INPUT_VOLT_OFFSET):
        device.write(f'C{INPUT_VOLTAGE_CHANNEL}:OFFSET {VoltsOffset_inV}V')
        time.sleep(0.25)
        device.write(
            f'C{INPUT_VOLTAGE_CHANNEL}:VOLT_DIV {VoltsPerDivision_inV*1000}mV')
        print(f'IN VOLT OFFSET Old:{INPUT_VOLT_OFFSET}, New:{VoltsOffset_inV}')
        print(f'IN VOLT DIV Old:{INPUT_VOLT_DIV}, New:{VoltsPerDivision_inV}')
        INPUT_VOLT_OFFSET = VoltsOffset_inV
        INPUT_VOLT_DIV = VoltsPerDivision_inV

    # INPUT AMPS
    # Calculate peak amps
    AmpsPerDivision_inA = math.ceil(targetCurrentRms*1.4*1.5/4)

    if (AmpsPerDivision_inA != INPUT_AMP_DIV):
        device.write(
            f'C{INPUT_CURRENT_CHANNEL}:VOLT_DIV {AmpsPerDivision_inA*1000}mV')
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


def processBinaryData(Waveform, Div, Offset):
    result = []
    # convert raw data to voltage, P142 in prog manual
    for item in Waveform:
        if item > 127:
            result.append((item - 255) * (Div/25) - Offset)
        else:
            result.append(item * Div/25 - Offset)
    return result


def createTimeArray(Samples, Div, Delay, Sparsing):
    ################# TIME PROCESS #################
    SAMPLE_RATE = device.query('SAMPLE_RATE?')
    SAMPLE_RATE = float(SAMPLE_RATE[len('SARA '):-5])
    Time_Interval_ms = 1 / SAMPLE_RATE * 1000

    # get time interval, P143 in prog manual
    Initial_Time_Value = Delay + (Div * 14/2)

    # build time axis array
    output = []
    for i in range(Samples):
        if i == 0:
            output.append(Initial_Time_Value)
        elif i > 0:
            output.append(output[0] + (Time_Interval_ms * Sparsing)*i)
    output = np.array(output)
    return output


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
    output.capturerawlength = len(VOLTAGE_WAVEFORM)

    if (output.capturerawlength != 0):
        ################# Process Waveform #################
        VOLTAGE_RESULT = processBinaryData(
            VOLTAGE_WAVEFORM, VOLT_DIV, VOLT_OFFSET)
        CURRENT_RESULT = processBinaryData(
            CURRENT_WAVEFORM, AMP_DIV, AMP_OFFSET)
        TIME_AXIS = createTimeArray(
            output.capturerawlength, TIME_DIV, TRIG_DELAY, Sparsing)

        # Trim to length of one cycle
        [idx_start, _] = findClosestValue(TIME_AXIS, 0)
        [idx_end, _] = findClosestValue(TIME_AXIS, (Time_Scale/1000))

        TIME_AXIS = np.array(TIME_AXIS[idx_start:idx_end])
        VOLTAGE_RESULT = np.array(VOLTAGE_RESULT[idx_start:idx_end])
        CURRENT_RESULT = np.array(CURRENT_RESULT[idx_start:idx_end])
        POWER_RESULT = np.multiply(VOLTAGE_RESULT, CURRENT_RESULT)

        output_raw = oscilloscoperawdata()
        output_raw.time_array = TIME_AXIS
        output_raw.voltage_array = VOLTAGE_RESULT
        output_raw.current_array = CURRENT_RESULT
        output_raw.power_array = POWER_RESULT

        output.capturetrimlength = len(output_raw.voltage_array)
        output.errortime = abs(
            round((Time_Scale/1000 - output_raw.time_array[-1])/(Time_Scale/1000)*100, 2))

        output.current_pk = round(
            float(np.percentile(output_raw.current_array, 95)), 2)
        output.current_rms = round(
            np.sqrt(np.mean(np.square(output_raw.current_array))), 3)
        output.current_av = round(
            float(np.average(np.absolute(output_raw.current_array))), 3)

        output.voltage_pk = round(
            float(np.percentile(output_raw.voltage_array, 95)), 2)
        output.voltage_rms = round(
            np.sqrt(np.mean(np.square(output_raw.voltage_array))), 2)
        output.voltage_av = round(
            float(np.average(np.absolute(output_raw.voltage_array))), 3)

        output.power_pk = round(
            float(np.percentile(output_raw.power_array, 95)), 2)
        output.power_rms = round(
            np.sqrt(np.mean(np.square(output_raw.power_array))), 3)
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

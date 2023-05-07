import pyvisa as visa
import numpy as np
import math
import time
import sys
import re
from dataclasses import dataclass


@dataclass
class channelconfiguration:
    id: int = 0
    enabled: bool = False
    name: str = ''
    div: int = 0
    offset: int = 0
    attn: int = 0
    unit: str = ''
    data: np.ndarray = np.array([])


@dataclass
class timeconfiguration:
    div: int = 0
    delay: int = 0
    samplerate: int = 0
    sharedchannels: int = 0
    sparsing: int = 0


@dataclass
class oscilloscopedata:
    capturetime: float = 0
    errorcounts: int = 0
    errorpct: float = 0
    capturerawlength: int = 0
    capturetrimlength: int = 0
    sparsing: int = 0
    ampout_av: float = 0
    ampout_rms: float = 0
    ampout_pk: float = 0
    voltout_av: float = 0
    voltout_rms: float = 0
    voltout_pk: float = 0
    powerout_av: float = 0
    powerout_rms: float = 0
    powerout_pk: float = 0
    voltin_av: float = 0
    voltin_rms: float = 0
    voltin_pk: float = 0
    ampin_av: float = 0
    ampin_rms: float = 0
    ampin_pk: float = 0
    powerin_av: float = 0
    powerin_rms: float = 0
    powerin_pk: float = 0

@dataclass
class recordsummary:
    average: float = 0
    rms: float = 0
    max: float = 0
    min: float = 0

@dataclass
class oscilloscoperawdata:
    time_array: np.ndarray = np.array([])
    voltin_array: np.ndarray = np.array([])
    ampin_array: np.ndarray = np.array([])
    powerin_array: np.ndarray = np.array([])
    voltout_array: np.ndarray = np.array([])
    ampout_array: np.ndarray = np.array([])
    powerout_array: np.ndarray = np.array([])


TIME_INFO = timeconfiguration()
CHANNEL_LIST = [channelconfiguration(id=1, enabled=True, name='VOLT_OUT', attn=10, unit='V'),
                channelconfiguration(id=2, enabled=True, name='AMP_OUT', attn=10, unit='A'),
                channelconfiguration(id=3, enabled=True, name='VOLT_IN', attn=10, unit='V'),
                channelconfiguration(id=4, enabled=True, name='AMP_IN', attn=10, unit='A', offset=-1)]


try:
    rm = visa.ResourceManager()
    # device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    device = rm.open_resource('TCPIP::192.168.1.128::INSTR', query_delay=0.25)

except Exception:
    print('      Failed to connect to oscilloscope')
    sys.exit(0)
device.timeout = 10000


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

    setTrigger(CHANNEL_LIST[1].id, 100)

    for i in range(len(CHANNEL_LIST)):
        if CHANNEL_LIST[i].enabled is True:
            configureChannel(
                CHANNEL_LIST[i].id, CHANNEL_LIST[i].attn, CHANNEL_LIST[i].offset, CHANNEL_LIST[i].unit)
            time.sleep(0.1)


def captureAllSingle(Samples, Time_Scale):
    start_time = time.perf_counter()

    configureScopeHorizontalAxis(Time_Scale)
    TIME_INFO.sparsing = setSparsing(Samples, Time_Scale)

    # Setup waveform capture
    device.write(str.format(f'WAVEFORM_SETUP SP,{TIME_INFO.sparsing},NP,{Samples},FP,0'))
    # Start Capture
    time.sleep(1)
    device.write('ARM')
    device.write('WAIT')
    time.sleep(1)

    ################# Capture Data #################
    VOLTAGE_WAVEFORM = []
    error_counts = 0

    while ((len(VOLTAGE_WAVEFORM) == 0) & (error_counts == 0)):
        collectOscilloscopeData()
        VOLTAGE_WAVEFORM = CHANNEL_LIST[0].data
        if (len(CHANNEL_LIST[0].data) == 0):
            print(
                f'Missed Data: Error - {error_counts}, Length - {len(VOLTAGE_WAVEFORM)}')
            error_counts += 1

    output = oscilloscopedata()
    output.capturerawlength = len(VOLTAGE_WAVEFORM)

    if (output.capturerawlength != 0):
        ################# Process Waveform #################
        TIME_AXIS = createTimeArray(
            output.capturerawlength, TIME_INFO.div, TIME_INFO.delay, TIME_INFO.sparsing)
        
        # Trim to length of one cycle
        [idx_start, _] = findClosestValue(TIME_AXIS, 0)
        [idx_end, _] = findClosestValue(TIME_AXIS, (Time_Scale/1000))

        VOLTAGE_RESULT = processBinaryData(
            CHANNEL_LIST[0].data, CHANNEL_LIST[0].div, CHANNEL_LIST[0].offset)
        CURRENT_RESULT = processBinaryData(
            CHANNEL_LIST[1].data, CHANNEL_LIST[1].div, CHANNEL_LIST[1].offset)
        VOLT_IN_RESULT = processBinaryData(
            CHANNEL_LIST[2].data, CHANNEL_LIST[2].div, CHANNEL_LIST[2].offset)
        AMP_IN_RESULT = processBinaryData(
            CHANNEL_LIST[3].data, CHANNEL_LIST[3].div, CHANNEL_LIST[3].offset)

        TIME_AXIS = np.array(TIME_AXIS[idx_start:idx_end])
        VOLTAGE_RESULT = np.array(VOLTAGE_RESULT[idx_start:idx_end])
        CURRENT_RESULT = np.array(CURRENT_RESULT[idx_start:idx_end])
        VOLT_IN_RESULT = np.array(VOLT_IN_RESULT[idx_start:idx_end])
        AMP_IN_RESULT = np.array(AMP_IN_RESULT[idx_start:idx_end])
        POWER_RESULT = np.multiply(VOLTAGE_RESULT, CURRENT_RESULT)
        POWER_IN_RESULT = np.multiply(VOLT_IN_RESULT, AMP_IN_RESULT)

        output_raw = oscilloscoperawdata()
        output_raw.time_array = TIME_AXIS
        output_raw.voltout_array = VOLTAGE_RESULT
        output_raw.ampout_array = CURRENT_RESULT
        output_raw.powerout_array = POWER_RESULT
        output_raw.voltin_array = VOLT_IN_RESULT
        output_raw.ampin_array = AMP_IN_RESULT
        output_raw.powerin_array = POWER_IN_RESULT

        output.capturetrimlength = len(output_raw.voltin_array)
        output.errorpct = abs(
            round((Time_Scale/1000 - output_raw.time_array[-1])/(Time_Scale/1000)*100, 2))

        output.ampout_pk = round(
            float(np.percentile(output_raw.ampout_array, 95)), 2)
        output.ampout_rms = round(
            np.sqrt(np.mean(np.square(output_raw.ampout_array))), 3)
        output.ampout_av = round(
            float(np.average(np.absolute(output_raw.ampout_array))), 3)

        output.voltout_pk = round(
            float(np.percentile(output_raw.voltout_array, 95)), 2)
        output.voltout_rms = round(
            np.sqrt(np.mean(np.square(output_raw.voltout_array))), 2)
        output.voltout_av = round(
            float(np.average(np.absolute(output_raw.voltout_array))), 3)

        output.powerout_pk = round(
            float(np.percentile(output_raw.powerout_array, 95)), 2)
        output.powerout_rms = round(
            np.sqrt(np.mean(np.square(output_raw.powerout_array))), 3)
        output.powerout_av = round(float(np.average(output_raw.powerout_array)*2), 2)

        output.voltin_pk = round(
            float(np.percentile(output_raw.voltin_array, 95)), 2)
        output.voltin_rms = round(
            np.sqrt(np.mean(np.square(output_raw.voltin_array))), 3)
        output.voltin_av = round(
            float(np.average(np.absolute(output_raw.voltin_array))), 3)

        output.ampin_pk = round(
            float(np.percentile(output_raw.ampin_array, 95)), 2)
        output.ampin_rms = round(
            np.sqrt(np.mean(np.square(output_raw.ampin_array))), 2)
        output.ampin_rms = round(
            float(np.average(np.absolute(output_raw.ampin_array))), 3)

        output.capturetime = round(time.perf_counter() - start_time, 2)

    else:
        output_raw = oscilloscoperawdata()

    output.sparsing = TIME_INFO.sparsing
    output.errorcounts = error_counts

    return output, output_raw



def collectOscilloscopeData():

    # send capture to controller
    for i in range(len(CHANNEL_LIST)):
        if (CHANNEL_LIST[i].enabled is True):
            device.write(f'C{CHANNEL_LIST[i].id}:WAVEFORM? DAT2')

    # send capture to controller
    device.chunk_size = 1024*1024*1024

    # read capture from controller
    for i in range(len(CHANNEL_LIST)):
        if (CHANNEL_LIST[i].enabled is True):
            CHANNEL_LIST[i].data = device.query_binary_values(str.format(
                f'C{CHANNEL_LIST[i].id}:WAVEFORM? DAT2'), datatype='s', is_big_endian=False)

def configureScopeHorizontalAxis(CaptureTime_us):
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
    if (TimePerDivision_us != TIME_INFO.div):
        device.write(f'TIME_DIV {TimePerDivision_us}US')
        device.write(f'TRIG_DELAY {TriggerDelay_us}US')
        TIME_INFO.div = TimePerDivision_us
        TIME_INFO.delay = TriggerDelay_us

def configureScopeVerticalAxis(inputVoltage, targetCurrentRms):

    # Output Volts -> mV -> 4 sections -> 200% of data
    VoltsPerDivision_outV = math.ceil(inputVoltage/4*2)
    updateVDIV(CHANNEL_LIST[0], VoltsPerDivision_outV)

    # Output Amps -> A -> 4 sections -> Arms to Apkpk -> 150% of data
    AmpsPerDivision_outA = math.ceil(targetCurrentRms*10/4*1.4*1.5)/10
    updateVDIV(CHANNEL_LIST[1], AmpsPerDivision_outA)

    # INPUT_VOLTS
    # Set Scaling so that the display shows +/-50% of input voltage
    VoltsPerDivision_inV = math.ceil(inputVoltage*.20 / 8)
    updateVDIV(CHANNEL_LIST[2], VoltsPerDivision_inV)

    # Set Offset Equal to Input Voltage so trace is centered in display
    VoltsOffset_inV = -inputVoltage + VoltsPerDivision_inV
    updateOFFSET(CHANNEL_LIST[2], VoltsOffset_inV)

    # INPUT AMPS - Calculate peak amps
    AmpsPerDivision_inA = math.ceil(targetCurrentRms*1.4*1.5/4)
    updateVDIV(CHANNEL_LIST[3], AmpsPerDivision_inA)

###################### Support Functions ######################

def setTrigger(ChannelID, LevelmV):
    # Set Trigger Mode
    device.write('TRIG_MODE NORMAL')
    # Set Trigger Level to 0V
    device.write(f'C{ChannelID}:TRIG_LEVEL {LevelmV}mV')
    # Set Trigger Coupling to AC
    device.write(f'C{ChannelID}:TRIG_COUPLING DC')
    # Set Trigger Select to EDGE and Current Channel
    device.write(f'TRIG_SELECT EDGE, SR, C{ChannelID}')
    # Set Trigger Slope Positive
    device.write(f'C{ChannelID}:TRIG_SLOPE POS')

def configureChannel(ChannelID, Attenuation, OffsetV, Unit):
    # Set Voltage Channel to Volts
    device.write(f'C{ChannelID}:UNIT {Unit}')
    # Set Voltage Channel to 10X
    device.write(f'C{ChannelID}:ATTENUATION {Attenuation}')
    # Set Voltage Channel to DC Coupling
    device.write(f'C{ChannelID}:COUPLING D1M')
    # Set Voltage Channel Vertical Offset to 0
    device.write(f'C{ChannelID}:OFFSET {OffsetV}V')

def initializeChannels(channel_list):
    for i in range(len(channel_list)):
        if (channel_list[i].enabled is False):
            device.write(f'C{channel_list[i].id}:TRACE OFF')
        else:
            device.write(f'C{channel_list[i].id}:TRACE ON')

def findSharedChannels(channel_list):
    if (((channel_list[0].enabled is True) & (channel_list[1].enabled is True)) |
       ((channel_list[2].enabled is True) & (channel_list[3].enabled is True))):
        TIME_INFO.sharedchannels = 2
    else:
        TIME_INFO.sharedchannels = 1

def setSparsing(Samples, Time_Scale):
    if (TIME_INFO.div == 20000):
        Sparsing = int(np.ceil(Time_Scale/(Samples/50)/TIME_INFO.sharedchannels))
    elif (TIME_INFO.div == 10000):
        Sparsing = int(np.ceil(Time_Scale/(Samples/100)/TIME_INFO.sharedchannels))
    elif (TIME_INFO.div == 5000):
        # At 5ms/div, we have 17.5M samples per screen instead of just 14
        Sparsing = int(np.ceil(Time_Scale*17.5/14 /
                       (Samples/200)/TIME_INFO.sharedchannels))
    elif (TIME_INFO.div == 2000):
        Sparsing = int(np.ceil(Time_Scale/(Samples/500)/TIME_INFO.sharedchannels))
    else:
        Sparsing = int(np.ceil(Time_Scale/(Samples/1000)/TIME_INFO.sharedchannels))

    return Sparsing

def createTimeArray(Samples, Div, Delay, Sparsing):
    ################# TIME PROCESS #################
    TIME_INFO.samplerate = device.query('SAMPLE_RATE?')
    TIME_INFO.samplerate = float(TIME_INFO.samplerate[len('SARA '):-5])
    Time_Interval_ms = 1 / TIME_INFO.samplerate * 1000

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

def parseOscilloscopeResponse(response):
    match = re.search(r'([-+]?\d*\.\d+([eE][-+]?\d+)?)', response)

    if match:
        processedResponse = float(match.group(1))
    else:
        processedResponse = None
    return processedResponse

def updateVDIV(channel, newvdiv):
    if (newvdiv != channel.div):
        device.write(f'C{channel.id}:VOLT_DIV {newvdiv}V')
        print(f'{channel.name} VDIV Old:{channel.div}, New:{newvdiv}')
        channel.div = newvdiv

def updateOFFSET(channel, newoffset):
    if (newoffset != channel.offset):
        device.write(f'C{channel.id}:OFFSET {newoffset}V')
        print(f'{channel.name} OFFSET Old:{channel.offset}, New:{newoffset}')
        channel.offset = newoffset

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

def processBinaryData(Waveform, Div, Offset):
    result = []
    # convert raw data to voltage, P142 in prog manual
    for item in Waveform:
        if item > 127:
            result.append((item - 255) * (Div/25) - Offset)
        else:
            result.append(item * Div/25 - Offset)
    return result

# def parameterMeasureStart():
#     # Set Up Voltage Measurement
#     device.write('PARAMETER_CLR')

#     device.write(f'PARAMETER_CUSTOM RMS, C{VOLTAGE_CHANNEL}')
#     device.write(f'PARAMETER_CUSTOM PKPK, C{VOLTAGE_CHANNEL}')

#     # Set Up Current measurement:
#     device.write(f'PARAMETER_CUSTOM RMS, C{CURRENT_CHANNEL}')
#     device.write(f'PARAMETER_CUSTOM PKPK, C{CURRENT_CHANNEL}')

#     # Set Up Math Measurement
#     device.write("'DEFINE_EQN, 'C1*C3'")


# def parameterMeasureRead():
#     # Read Voltage
#     volt_rms = parseOscilloscopeResponse(device.query(
#         f'C{VOLTAGE_CHANNEL}:PARAMETER_VALUE? RMS'))
#     volt_pk = parseOscilloscopeResponse(device.query(
#         f'C{VOLTAGE_CHANNEL}:PARAMETER_VALUE? PKPK'))

#     # Read Current
#     current_rms = parseOscilloscopeResponse(
#         device.query(f'C{CURRENT_CHANNEL}:PARAMETER_VALUE? RMS'))
#     current_pk = parseOscilloscopeResponse(
#         device.query(f'C{CURRENT_CHANNEL}:PARAMETER_VALUE? PKPK'))
#     return volt_rms, volt_pk, current_rms, current_pk

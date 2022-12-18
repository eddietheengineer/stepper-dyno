import sys
import pyvisa as visa
import numpy as np
import matplotlib.pyplot as plotter

try:
    rm = visa.ResourceManager()

    # Connect to device (Make sure to change the resource locator!)
    #device = rm.open_resource('USB0::62700::60984::SDSMMGKC6R0277::0::INSTR',query_delay=0.25)
    device = rm.open_resource('TCPIP::10.10.10.163::INSTR',query_delay=0.25)

except:
    print('Failed to connect to device...')
    sys.exit(0)
device.timeout = 30000

CHAN = 1
SAMPLE_RATE = device.query('SARA?')
SAMPLE_RATE = float(SAMPLE_RATE[len('SARA '):-5])

TIME_DIV = device.query('TDIV?')
TIME_DIV = float(TIME_DIV[len('TDIV '):-2])

TRIG_DELAY = device.query('TRDL?')
TRIG_DELAY = float(TRIG_DELAY[len('TRDL '):-2])

VOLT_DIV = device.query('C1:Volt_DIV?')
VOLT_DIV = float(VOLT_DIV[len('C1:VDIV '):-2])

VOLT_OFFSET = device.query('C1:OFfSeT?')
VOLT_OFFSET = float(VOLT_OFFSET[len('C1:OFST '):-2])

# Setup waveform capture
device.write('WFSU SP,10000,NP,10000,FP,0')

#send capture to controller
device.write('C1:WF? DAT2')
device.chunk_size = 1024*1024*1024

# read capture from controller
WAVEFORM = device.query_binary_values('C1:WF? DAT2', datatype='s', is_big_endian=False)
RESULT = []
#convert raw data to voltage, P142 in prog manual
for item in WAVEFORM:
    if item > 127:
        RESULT.append((item - 255) * (VOLT_DIV/25) - VOLT_OFFSET)
    else:
        RESULT.append(item * VOLT_DIV/25 - VOLT_OFFSET)

#get time interval, P143 in prog manual
TIME_VALUE = TRIG_DELAY - (TIME_DIV * 14/2)
TIME_INTERVAL = 1 / SAMPLE_RATE

#build time axis array
TIME_AXIS = []
for i in range(len(RESULT)):
    if i ==0:
        TIME_AXIS.append(TIME_VALUE)
    elif i > 0:
        TIME_AXIS.append(TIME_AXIS[0] + (TIME_INTERVAL * 10000)*i)

# plot data
plotter.plot(TIME_AXIS, RESULT)
plotter.title('Waveformfrom  from SDS1204X-E')
plotter.xlabel("Time")
plotter.ylabel("Volts")
plotter.yticks(np.arange(VOLT_DIV*(-4),VOLT_DIV*4+1,VOLT_DIV))
plotter.xticks(np.arange(TIME_AXIS[0],TIME_AXIS[len(TIME_AXIS)-1],TIME_DIV))
plotter.xticks(rotation = 90)
plotter.ylim(VOLT_DIV*(-4), VOLT_DIV*(4))
plotter.margins(0)
plotter.grid('True')
plotter.show()
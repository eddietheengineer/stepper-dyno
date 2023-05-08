import numpy as np
import matplotlib.pyplot as plotter
from dataclasses import dataclass
import csv

voltageindex = 3
microstepindex = 4
currentindex = 5
speedindex = 6


@dataclass
class testchunk:
    axisspeed: np.ndarray = np.array([])
    axisvalues: np.ndarray = np.array([])
    voltage: int = 0
    microstep: int = 0
    current: float = 0
    linetype: str = ''
    color: str = ''


def readfile(model_number, test_id):
    filename = f'/home/pi/Desktop/{model_number}_{test_id}/{model_number}_{test_id}_Summary.csv'
    with open(filename, encoding='UTF-8') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter = ',',quotechar = "'", skipinitialspace = True)
        header = []
        for row in csv_reader:
            header = row
            break
    data = np.genfromtxt(filename, delimiter=',')
    return header, data


def parsetestparameters(array):
    voltages = tuple(generateuniquevalues(array[1:, voltageindex]))
    microsteps = tuple(generateuniquevalues(array[1:, microstepindex]))
    currents = tuple(generateuniquevalues(array[1:, currentindex]))
    currentsx100 = [int(element*100) for element in currents]
    return voltages, microsteps, currentsx100


def generateuniquevalues(array):
    output = list(set(array))
    output.sort(reverse=True)
    return output


def findindex(data):
    indices = []
    for x in range(1, len(data)):
        if (data[x, speedindex] < data[(x-1), speedindex]):
            indices.append(x)
    return indices


def split(array):
    idx = findindex(array)
    array = np.split(array, idx)
    return array


def generatechunks(sarray, index, speedindex):
    groupdata = []
    for i, chunk in enumerate(sarray):
        groupdata.append(testchunk())
        groupdata[i].axisspeed = np.array(chunk[:, speedindex])
        groupdata[i].axisvalues = np.array(chunk[:, index])
        groupdata[i].voltage = int(chunk[1, voltageindex])
        groupdata[i].microstep = int(chunk[1, microstepindex])
        groupdata[i].current = int(chunk[1, currentindex]*100)
    return groupdata


def plotcolortype(originalarray, groupdata):
    voltagevalues, _, currentvalues = parsetestparameters(originalarray)
    # voltage_linestyles = [':', '-.', '--', '-']
    voltage_linestyles = ['-', '--', '-.', ':']
    current_colors = ['red', 'orange', 'green', 'blue',
                      'darkviolet', 'black', 'grey', 'magenta', 'deepskyblue']
    for i, _ in enumerate(groupdata):
        groupdata[i].linetype = voltage_linestyles[voltagevalues.index(
            groupdata[i].voltage)]
        groupdata[i].color = current_colors[currentvalues.index(
            groupdata[i].current)]


def generateplot(modelnumber, testid, valueid, title, yaxislabel):
    # Read in file
    header, array = readfile(modelnumber, testid)
    valueindex = header.index(valueid)

    # spilt array into chunks
    splitarray = split(array)
    splitarray.reverse()

    # Convert chunks into dataclass objects
    chunkdata = generatechunks(splitarray, valueindex, speedindex)

    # Read dataclass objects and add linestyle and color formatting values
    plotcolortype(array, chunkdata)
    maxspeed = 0

    plotter.rcParams['figure.figsize'] = [8, 4.5]
    plotter.margins(0)
    plotter.grid(visible=True)

    for _, chunk in enumerate(chunkdata):
        label = f'{chunk.voltage}V {chunk.current/100}A'
        plotter.plot(chunk.axisspeed, chunk.axisvalues, color=chunk.color,
                     linestyle=chunk.linetype, label=label, linewidth=0.9)
        maxspeed_test = np.amax(chunk.axisspeed)
        if (maxspeed_test > maxspeed):
            maxspeed = maxspeed_test
    plot_title = f'{modelnumber} {testid} {title}'

    plotter.legend()
    plotter.title(f'{plot_title}')
    plotter.xlabel("Speed (mm/s)")
    # add 30% buffer to give space for the legend
    plotter.xlim(0, (maxspeed*1.3))
    plotter.ylabel(yaxislabel)
    plotter.ylim(bottom=0)
    plotter.savefig(
        f'/home/pi/Desktop/{modelnumber}_{testid}/{plot_title}.png', dpi=240)
    plotter.clf()
    plotter.close()

def generateplots(modelnumber, testid):
    generateplot(modelnumber, testid, 'psu.measuredpower', 'Driver Input Power', 'Power (W)')
    generateplot(modelnumber, testid, 'scope.powerout_av', 'Driver Output Power', 'Power (W)')
    generateplot(modelnumber, testid, 'mech.motorpower', 'Mechanical Motor Power', 'Power (W)')
    generateplot(modelnumber, testid, 'scope.ampout_rms', 'Stepper Current (RMS)', 'Current (A)')

    generateplot(modelnumber, testid,  'powersummary.driverpower_loss', 'Driver Power Loss', 'Power (W)')
    generateplot(modelnumber, testid,  'powersummary.motorpower_totalloss', 'Stepper Motor Total Loss', 'Power (W)')
    generateplot(modelnumber, testid,  'powersummary.motorpower_copperloss', 'Stepper Motor Copper Loss', 'Power (W)')
    generateplot(modelnumber, testid,  'powersummary.motorpower_ironloss', 'Stepper Motor Iron Loss', 'Power (W)')

import numpy as np
import matplotlib.pyplot as plotter


def findindex(data):
    indices = []
    for x in range(1, len(data)):
        if (data[x, 4] < data[(x-1), 4]):
            indices.append(x)
    return indices


def outputdata(model_number, test_id):
    filename = f'/home/pi/Desktop/{model_number}/{model_number}_{test_id}_Summary.csv'
    data = np.genfromtxt(filename, delimiter=',')
    idx = findindex(data)
    array = np.split(data, idx)
    return array


def defineindexes(model_number, test_id):
    array = outputdata(model_number, test_id)
    voltages = []
    currents = []
    for _, value in enumerate(array):
        voltages.append(value[1, 2])
        currents.append(value[1, 3])
    return voltages, currents


def plotcolortype(voltage, current):
    voltage_linestyles = [[12, 24, 36, 48], [':', '-.', '--', '-']]
    current_colors = [[0.4, 0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0], [
        'magenta', 'darkviolet', 'blue', 'deepskyblue', 'green', 'orange', 'red', 'grey', 'black']]
    linestyle = voltage_linestyles[1][voltage_linestyles[0].index(voltage)]
    color = current_colors[1][current_colors[0].index(current)]
    return linestyle, color


def plotSummaryDataNew(model_number):
    output_data = outputdata(model_number, test_id)
    (voltages, currents) = defineindexes(model_number, test_id)
    speed_index = 4

    tests = [['Driver Power', 'RMS Current',
              'RMS Voltage', 'Test Point Torque']]
    plot_index = 8

    maxspeed = 0
    for x in range(len(output_data)):
        label = '%s_%s' % (voltages[x], currents[x])
        (linestyle, color) = plotcolortype(voltages[x], currents[x])
        plotter.plot(output_data[x][0:-1, speed_index], output_data[x]
                     [0:-1, plot_index], color=color, label=label, linestyle=linestyle)
        maxspeed_test = np.amax(output_data[x][:, speed_index])
        if (maxspeed_test > maxspeed):
            maxspeed = maxspeed_test
    plot_title = '%s Driver Power' % model_number
    plotter.legend()
    plotter.margins(0)
    plotter.grid('True')
    plotter.title('%s' % (plot_title))
    plotter.xlabel("Speed (mm/s)")
    plotter.xlim(0, (maxspeed+200))
    plotter.ylabel("Driver Power (W)")
    plotter.savefig('/home/pi/Desktop/%s/%s_Test.png' %
                    (model_number, plot_title), dpi=300)
    plotter.clf()
    plotter.close()


def plotSummaryData(model_number, test_id):
    output_data = outputdata(model_number, test_id)
    data246 = output_data[0]
    data248 = output_data[1]
    data2410 = output_data[2]
    data2412 = output_data[3]
    data2414 = output_data[4]
    data366 = output_data[5]
    data368 = output_data[6]
    data3610 = output_data[7]
    data3612 = output_data[8]
    data3614 = output_data[9]
    data486 = output_data[10]
    data488 = output_data[11]
    data4810 = output_data[12]
    data4812 = output_data[13]
    data4814 = output_data[14]

    speed_index = 4
    plot_index = 8
    plot_title = f'{model_number} Driver Power'

    plotter.plot(data246[:, speed_index], data246[:,
                 plot_index], 'blue', label='24_0.6', linestyle=':')
    plotter.plot(data248[:, speed_index], data248[:, plot_index],
                 'orange', label='24_0.8', linestyle=':')
    plotter.plot(data2410[:, speed_index], data2410[:,
                 plot_index], 'green', label='24_1.0', linestyle=':')
    plotter.plot(data2412[:, speed_index], data2412[:,
                 plot_index], 'red', label='24_1.2', linestyle=':')
    plotter.plot(data2414[:, speed_index], data2414[:,
                 plot_index], 'purple', label='24_1.4', linestyle=':')

    plotter.plot(data366[:, speed_index], data366[:,
                 plot_index], 'blue', label='36_0.6', linestyle='--')
    plotter.plot(data368[:, speed_index], data368[:, plot_index],
                 'orange', label='36_0.8', linestyle='--')
    plotter.plot(data3610[:, speed_index], data3610[:,
                 plot_index], 'green', label='36_1.0', linestyle='--')
    plotter.plot(data3612[:, speed_index], data3612[:,
                 plot_index], 'red', label='36_1.2', linestyle='--')
    plotter.plot(data3614[:, speed_index], data3614[:,
                 plot_index], 'purple', label='36_1.4', linestyle='--')

    plotter.plot(data486[:, speed_index], data486[:,
                 plot_index], 'blue', label='48_0.6')
    plotter.plot(data488[:, speed_index], data488[:,
                 plot_index], 'orange', label='48_0.8')
    plotter.plot(data4810[:, speed_index], data4810[:,
                 plot_index], 'green', label='48_1.0')
    plotter.plot(data4812[:, speed_index],
                 data4812[:, plot_index], 'red', label='48_1.2')
    plotter.plot(data4814[:, speed_index], data4814[:,
                 plot_index], 'purple', label='48_1.4')
    plotter.legend()
    plotter.margins(0)
    plotter.grid('True')

    plotter.title(f'{plot_title}')
    plotter.xlabel("Speed (mm/s)")
    plotter.ylabel("Driver Power (W)")

    plotter.savefig(
        f'/home/pi/Desktop/{model_number}/{plot_title}.png', dpi=300)
    plotter.clf()
    plotter.close()

    speed_index = 4
    plot_index = 9
    plot_title = f'{model_number} RMS Current'

    plotter.plot(data246[:, speed_index], data246[:,
                 plot_index], 'blue', label='24_0.6', linestyle=':')
    plotter.plot(data248[:, speed_index], data248[:, plot_index],
                 'orange', label='24_0.8', linestyle=':')
    plotter.plot(data2410[:, speed_index], data2410[:,
                 plot_index], 'green', label='24_1.0', linestyle=':')
    plotter.plot(data2412[:, speed_index], data2412[:,
                 plot_index], 'red', label='24_1.2', linestyle=':')
    plotter.plot(data2414[:, speed_index], data2414[:,
                 plot_index], 'purple', label='24_1.4', linestyle=':')

    plotter.plot(data366[:, speed_index], data366[:,
                 plot_index], 'blue', label='36_0.6', linestyle='--')
    plotter.plot(data368[:, speed_index], data368[:, plot_index],
                 'orange', label='36_0.8', linestyle='--')
    plotter.plot(data3610[:, speed_index], data3610[:,
                 plot_index], 'green', label='36_1.0', linestyle='--')
    plotter.plot(data3612[:, speed_index], data3612[:,
                 plot_index], 'red', label='36_1.2', linestyle='--')
    plotter.plot(data3614[:, speed_index], data3614[:,
                 plot_index], 'purple', label='36_1.4', linestyle='--')

    plotter.plot(data486[:, speed_index], data486[:,
                 plot_index], 'blue', label='48_0.6')
    plotter.plot(data488[:, speed_index], data488[:,
                 plot_index], 'orange', label='48_0.8')
    plotter.plot(data4810[:, speed_index], data4810[:,
                 plot_index], 'green', label='48_1.0')
    plotter.plot(data4812[:, speed_index],
                 data4812[:, plot_index], 'red', label='48_1.2')
    plotter.plot(data4814[:, speed_index], data4814[:,
                 plot_index], 'purple', label='48_1.4')
    plotter.legend()
    plotter.margins(0)
    plotter.grid('True')

    plotter.title('%s' % (plot_title))
    plotter.xlabel("Speed (mm/s)")
    plotter.ylabel("RMS Current (A)")

    plotter.savefig(
        f'/home/pi/Desktop/{model_number}/{plot_title}.png', dpi=300)
    plotter.clf()
    plotter.close()

    speed_index = 4
    plot_index = 11
    plot_title = f'{model_number} RMS Voltage'

    plotter.plot(data246[:, speed_index], data246[:,
                 plot_index], 'blue', label='24_0.6', linestyle=':')
    plotter.plot(data248[:, speed_index], data248[:, plot_index],
                 'orange', label='24_0.8', linestyle=':')
    plotter.plot(data2410[:, speed_index], data2410[:,
                 plot_index], 'green', label='24_1.0', linestyle=':')
    plotter.plot(data2412[:, speed_index], data2412[:,
                 plot_index], 'red', label='24_1.2', linestyle=':')
    plotter.plot(data2414[:, speed_index], data2414[:,
                 plot_index], 'purple', label='24_1.4', linestyle=':')

    plotter.plot(data366[:, speed_index], data366[:,
                 plot_index], 'blue', label='36_0.6', linestyle='--')
    plotter.plot(data368[:, speed_index], data368[:, plot_index],
                 'orange', label='36_0.8', linestyle='--')
    plotter.plot(data3610[:, speed_index], data3610[:,
                 plot_index], 'green', label='36_1.0', linestyle='--')
    plotter.plot(data3612[:, speed_index], data3612[:,
                 plot_index], 'red', label='36_1.2', linestyle='--')
    plotter.plot(data3614[:, speed_index], data3614[:,
                 plot_index], 'purple', label='36_1.4', linestyle='--')

    plotter.plot(data486[:, speed_index], data486[:,
                 plot_index], 'blue', label='48_0.6')
    plotter.plot(data488[:, speed_index], data488[:,
                 plot_index], 'orange', label='48_0.8')
    plotter.plot(data4810[:, speed_index], data4810[:,
                 plot_index], 'green', label='48_1.0')
    plotter.plot(data4812[:, speed_index],
                 data4812[:, plot_index], 'red', label='48_1.2')
    plotter.plot(data4814[:, speed_index], data4814[:,
                 plot_index], 'purple', label='48_1.4')
    plotter.legend()
    plotter.margins(0)
    plotter.grid('True')

    plotter.title(f'{plot_title}')
    plotter.xlabel("Speed (mm/s)")
    plotter.ylabel("RMS Voltage (V))")

    plotter.savefig(
        f'/home/pi/Desktop/{model_number}/{plot_title}.png', dpi=300)
    plotter.clf()
    plotter.close()

    speed_index = 4
    plot_index = 13
    plot_title = f'{model_number} Test Point Torque'

    plotter.plot(data246[:, speed_index], data246[:,
                 plot_index], 'blue', label='24_0.6', linestyle=':')
    plotter.plot(data248[:, speed_index], data248[:, plot_index],
                 'orange', label='24_0.8', linestyle=':')
    plotter.plot(data2410[:, speed_index], data2410[:,
                 plot_index], 'green', label='24_1.0', linestyle=':')
    plotter.plot(data2412[:, speed_index], data2412[:,
                 plot_index], 'red', label='24_1.2', linestyle=':')
    plotter.plot(data2414[:, speed_index], data2414[:,
                 plot_index], 'purple', label='24_1.4', linestyle=':')

    plotter.plot(data366[:, speed_index], data366[:,
                 plot_index], 'blue', label='36_0.6', linestyle='--')
    plotter.plot(data368[:, speed_index], data368[:, plot_index],
                 'orange', label='36_0.8', linestyle='--')
    plotter.plot(data3610[:, speed_index], data3610[:,
                 plot_index], 'green', label='36_1.0', linestyle='--')
    plotter.plot(data3612[:, speed_index], data3612[:,
                 plot_index], 'red', label='36_1.2', linestyle='--')
    plotter.plot(data3614[:, speed_index], data3614[:,
                 plot_index], 'purple', label='36_1.4', linestyle='--')

    plotter.plot(data486[:, speed_index], data486[:,
                 plot_index], 'blue', label='48_0.6')
    plotter.plot(data488[:, speed_index], data488[:,
                 plot_index], 'orange', label='48_0.8')
    plotter.plot(data4810[:, speed_index], data4810[:,
                 plot_index], 'green', label='48_1.0')
    plotter.plot(data4812[:, speed_index],
                 data4812[:, plot_index], 'red', label='48_1.2')
    plotter.plot(data4814[:, speed_index], data4814[:,
                 plot_index], 'purple', label='48_1.4')
    plotter.legend()
    plotter.margins(0)
    plotter.grid('True')

    plotter.title(f'{plot_title}')
    plotter.xlabel("Speed (mm/s)")
    plotter.ylabel("Test Torque (N-cm)")

    plotter.savefig(
        f'/home/pi/Desktop/{model_number}/{plot_title}.png', dpi=300)
    plotter.clf()
    plotter.close()

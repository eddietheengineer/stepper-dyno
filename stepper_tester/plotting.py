import matplotlib.pyplot as plotter
import os
import time
import numpy as np


def plotosData(alldata, array, type):
    start_time = time.perf_counter()
    Model_Number = alldata.id.stepper_model
    Test_ID = alldata.id.test_id
    Test_Number = alldata.id.test_counter
    Voltage = alldata.id.test_voltage
    Microstep = alldata.id.test_microstep
    Current = alldata.id.test_current
    Speed = alldata.id.test_speed

    Power = alldata.psu.measuredpower
    Current_RMS = alldata.scope.ampout_rms
    Torque = alldata.mech.torque

    Top_Line = f'Model: {Model_Number} Test ID: {Test_ID} Test Number: {Test_Number}'
    Middle_Line = f'Voltage: {Voltage} V, Microstep: {Microstep}, Current: {Current} A, Speed: {Speed} mm/s'
    #Bottom_Line = f'Power: {Power:0.1f}, Current (RMS): {Current_RMS:0.2f}, Torque: {Torque:0.1f}'

    plotter.rcParams['figure.figsize'] = [8, 4.5]
    fig, ax1 = plotter.subplots()
    ax2 = ax1.twinx()
    ax3 = ax1.twinx()
    if (type == 'Out'):
        ax1.plot(array.time_array, array.voltout_array, linewidth=0.5, label="Voltage")
        ax2.plot(array.time_array, array.ampout_array, linewidth=0.5, label="Current", color="orange")
        ax3.plot(array.time_array, array.powerout_array, linewidth=0.5, label="Power", color="red")
        ax1.set_ylim(-80, 80)
        ax2.set_ylim(-4, 4)
        ax3.set_ylim(-160, 160)
    elif (type == 'In'):
        halfcycle = round(len(array.time_array)/2)
        ax1.plot(array.time_array[:halfcycle], np.abs(array.voltout_array[:halfcycle]), linewidth=0.5, label="Stepper Voltage", color="orange")
        ax2.plot(array.time_array[:halfcycle], array.powerout_array[:halfcycle], linewidth=0.5, label="Stepper Power", color="red")
        ax3.plot(array.time_array[:halfcycle], array.voltin_array[:halfcycle], linewidth=0.5, label="Capacitor Voltage")
        ax1.set_ylim(Voltage*.8, Voltage*1.2)
        ax2.set_ylim(-160, 160)
        ax3.set_ylim(Voltage*.8, Voltage*1.2)
    plotter.title(f'{Top_Line} \n {Middle_Line}')
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Volts")

    ax2.set_ylabel("Amps")
    ax3.set_ylabel("Power")

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc=0)

    plotter.margins(0)
    plotter.grid(visible=True)

    filepath = f'/home/pi/Desktop/{Model_Number}_{Test_ID}/Oscilloscope_Plots_{type}/'

    if not os.path.exists(filepath):
        os.makedirs(filepath)

    filename = f'{Model_Number}_{Test_ID}_{Test_Number}_{Voltage}_{Microstep}_{Current}_{Speed}'
    plotter.savefig(f'{filepath}{filename}.png', dpi=240)
    plotter.clf()
    plotter.close()
    plot_time = time.perf_counter() - start_time
    return plot_time


# def plotSummaryData(output_data, index_data):
#     Model_Number = output_data[index_data.index('model_number')]
#     Index = output_data[index_data.index('test_id')]
#     Voltage = output_data[index_data.index('voltage_setting')]
#     Current = output_data[index_data.index('tmc_current')]
#     Speed = output_data[index_data.index('speed')]

#     P_Supply = output_data[index_data.index('p_supply')]
#     rms_current = output_data[index_data.index('current_rms')]
#     torque = output_data[index_data.index('torque')]

#     fig, ax1 = plotter.subplots()
#     ax2 = ax1.twinx()  # 24_8
#     ax3 = ax1.twinx()  # 24_10
#     ax4 = ax1.twinx()  # 24_12
#     ax5 = ax1.twinx()  # 24_14
#     ax6 = ax1.twinx()  # 36_6
#     ax7 = ax1.twinx()  # 36_8
#     ax8 = ax1.twinx()  # 36_10
#     ax9 = ax1.twinx()  # 36_12
#     ax10 = ax1.twinx()  # 36_14
#     ax11 = ax1.twinx()  # 48_6
#     ax12 = ax1.twinx()  # 48_8
#     ax13 = ax1.twinx()  # 48_10
#     ax14 = ax1.twinx()  # 48_12
#     ax15 = ax1.twinx()  # 48_14

#     ax1.plot(data246[0], data246[1], 'blue:')
#     ax2.plot(data248[0], data248[1], 'orange:')
#     ax3.plot(data2410[0], data2410[1], 'green:')
#     ax4.plot(data2412[0], data2412[1], 'red:')
#     ax5.plot(data2414[0], data2414[1], 'purple:')

#     ax6.plot(data246[0], data246[1], 'blue--')
#     ax7.plot(data248[0], data248[1], 'orange--')
#     ax8.plot(data2410[0], data2410[1], 'green--')
#     ax9.plot(data2412[0], data2412[1], 'red--')
#     ax10.plot(data2414[0], data2414[1], 'purple--')

#     ax11.plot(data246[0], data246[1], 'blue-')
#     ax12.plot(data248[0], data248[1], 'orange-')
#     ax13.plot(data2410[0], data2410[1], 'green-')
#     ax14.plot(data2412[0], data2412[1], 'red-')
#     ax15.plot(data2414[0], data2414[1], 'purple-')
#     plotter.show()

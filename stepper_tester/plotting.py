import matplotlib.pyplot as plotter
import os
import time


def plotosData(output_data, index_data, TIME_AXIS, RESULT1, RESULT2, RESULT3):
    start_time = time.perf_counter()
    Model_Number = output_data[index_data.index('model_number')]
    Test_ID = output_data[index_data.index('test_id')]
    Test_Number = output_data[index_data.index('test_counter')]
    Voltage = output_data[index_data.index('voltage_setting')]
    Microstep = output_data[index_data.index('microstep')]
    Current = output_data[index_data.index('tmc_current')]
    Speed = output_data[index_data.index('speed')]

    Power = output_data[index_data.index('p_supply')]
    Current_RMS = output_data[index_data.index('current_rms')]
    Current_PkPk = output_data[index_data.index('current_pkpk')]
    Torque = output_data[index_data.index('torque')]

    Top_Line = str('Model: %s Test ID: %s Test Number: %d' %
                   (Model_Number, Test_ID, Test_Number))
    Middle_Line = str('Voltage: %d V, Microstep: %d, Current: %0.2f A, Speed: %d mm/s' %
                      (Voltage, Microstep, Current, Speed))
    Bottom_Line = str('Power: %0.1f, Current (RMS): %0.2f, Current (Peak): %0.2f, Torque: %0.1f' % (
        Power, Current_RMS, Current_PkPk, Torque))

    plotter.rcParams['figure.figsize'] = [8, 4.5]
    fig, ax1 = plotter.subplots()
    ax2 = ax1.twinx()
    ax3 = ax1.twinx()
    ax1.plot(TIME_AXIS, RESULT1, linewidth=0.5, label="Voltage")
    ax2.plot(TIME_AXIS, RESULT2, linewidth=0.5,
             label="Current", color="orange")
    ax3.plot(TIME_AXIS, RESULT3, linewidth=0.5, label="Power", color="red")
    plotter.title('%s \n %s' % (Top_Line, Middle_Line))
    ax1.set_xlabel("Time (ms)")
    ax1.set_ylabel("Volts")
    ax1.set_ylim([-80, 80])
    ax2.set_ylabel("Amps")
    ax2.set_ylim([-4, 4])
    ax3.set_ylabel("Power")
    ax3.set_ylim([-160, 160])

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    lines3, labels3 = ax3.get_legend_handles_labels()
    ax1.legend(lines + lines2 + lines3, labels + labels2 + labels3, loc=0)

    plotter.margins(0)
    plotter.grid('True')

    filepath = '/home/pi/Desktop/%s_%s/Oscilloscope_Plots/' % (
        Model_Number, Test_ID)
    if not os.path.exists(filepath):
        os.makedirs(filepath)

    filename = str(Model_Number) + "_" + str(Test_ID) + "/Oscilloscope_Plots/" + str(Model_Number) + "_" + \
        str(Test_ID) + "_" + str(Test_Number)+"_"+str(Voltage) + \
        "_"+str(Microstep)+"_"+str(Current)+"_"+str(Speed)
    plotter.savefig(f'/home/pi/Desktop/{filename}.png', dpi=240)
    plotter.clf()
    plotter.close()
    plot_time = time.perf_counter() - start_time
    return plot_time


def plotSummaryData(output_data, index_data):
    Model_Number = output_data[index_data.index('model_number')]
    Index = output_data[index_data.index('test_id')]
    Voltage = output_data[index_data.index('voltage_setting')]
    Current = output_data[index_data.index('tmc_current')]
    Speed = output_data[index_data.index('speed')]

    P_Supply = output_data[index_data.index('p_supply')]
    rms_current = output_data[index_data.index('current_rms')]
    torque = output_data[index_data.index('torque')]

    fig, ax1 = plotter.subplots()
    ax2 = ax1.twinx()  # 24_8
    ax3 = ax1.twinx()  # 24_10
    ax4 = ax1.twinx()  # 24_12
    ax5 = ax1.twinx()  # 24_14
    ax6 = ax1.twinx()  # 36_6
    ax7 = ax1.twinx()  # 36_8
    ax8 = ax1.twinx()  # 36_10
    ax9 = ax1.twinx()  # 36_12
    ax10 = ax1.twinx()  # 36_14
    ax11 = ax1.twinx()  # 48_6
    ax12 = ax1.twinx()  # 48_8
    ax13 = ax1.twinx()  # 48_10
    ax14 = ax1.twinx()  # 48_12
    ax15 = ax1.twinx()  # 48_14

    ax1.plot(data246[0], data246[1], 'blue:')
    ax2.plot(data248[0], data248[1], 'orange:')
    ax3.plot(data2410[0], data2410[1], 'green:')
    ax4.plot(data2412[0], data2412[1], 'red:')
    ax5.plot(data2414[0], data2414[1], 'purple:')

    ax6.plot(data246[0], data246[1], 'blue--')
    ax7.plot(data248[0], data248[1], 'orange--')
    ax8.plot(data2410[0], data2410[1], 'green--')
    ax9.plot(data2412[0], data2412[1], 'red--')
    ax10.plot(data2414[0], data2414[1], 'purple--')

    ax11.plot(data246[0], data246[1], 'blue-')
    ax12.plot(data248[0], data248[1], 'orange-')
    ax13.plot(data2410[0], data2410[1], 'green-')
    ax14.plot(data2412[0], data2412[1], 'red-')
    ax15.plot(data2414[0], data2414[1], 'purple-')
    plotter.show()

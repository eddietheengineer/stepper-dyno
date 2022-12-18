import matplotlib.pyplot as plotter
import os		

def plotosData(output_data, TIME_AXIS, RESULT1, RESULT2):
	Model_Number = output_data[0]
	Index = output_data[1]
	Voltage = output_data[2]
	Current = output_data[3]
	Speed = output_data[4]
	fig, ax1 = plotter.subplots()
	ax2 = ax1.twinx()
	ax1.plot(TIME_AXIS, RESULT1, linewidth = 1)
	ax2.plot(TIME_AXIS, RESULT2, linewidth = 1, color = "orange")
	plotter.title('Model: %s, Voltage: %d, Current: %0.1f, Speed: %d' % (Model_Number, Voltage, Current, Speed))
	ax1.set_xlabel("Time (ms)")
	ax1.set_ylabel("Volts")
	ax1.set_ylim([-60,60])
	ax2.set_ylabel("Amps")
	ax2.set_ylim([-2,2])

	#plotter.legend()
	plotter.margins(0)
	plotter.grid('True')
	
	filepath = '/home/pi/Desktop/%s/Test_Plots/' % Model_Number 
	if not os.path.exists(filepath):
		os.makedirs(filepath)
	
	filename = str(Model_Number) + "/Test_Plots/" + str(Model_Number) + "_" + str(Index)+"_"+str(Voltage)+"_"+str(Current)+"_"+str(Speed)
	plotter.savefig('/home/pi/Desktop/%s.png' % filename, dpi=300)
	plotter.clf()
	plotter.close()
	
def plotSummaryData(output_data):
	Model_Number = output_data[0]
	Index = output_data[1]
	Voltage = output_data[2]
	Current = output_data[3]
	Speed = output_data[4]

	P_Supply = output_data[8]
	rms_current = output_data[10]
	torque = output_data[14]
	
	fig, ax1 = plotter.subplots()
	ax2 = ax1.twinx()	#24_8
	ax3 = ax1.twinx()	#24_10
	ax4 = ax1.twinx()	#24_12
	ax5 = ax1.twinx()	#24_14
	ax6 = ax1.twinx()	#36_6
	ax7 = ax1.twinx()	#36_8
	ax8 = ax1.twinx()	#36_10
	ax9 = ax1.twinx()	#36_12
	ax10 = ax1.twinx()	#36_14
	ax11 = ax1.twinx()	#48_6
	ax12 = ax1.twinx()	#48_8
	ax13 = ax1.twinx()	#48_10
	ax14 = ax1.twinx()	#48_12
	ax15 = ax1.twinx()	#48_14
	
	ax1.plot(data246[0],data246[1], 'blue:')
	ax2.plot(data248[0],data248[1], 'orange:')
	ax3.plot(data2410[0],data2410[1],'green:')
	ax4.plot(data2412[0],data2412[1],'red:')
	ax5.plot(data2414[0],data2414[1],'purple:')

	ax6.plot(data246[0],data246[1],'blue--')
	ax7.plot(data248[0],data248[1],'orange--')
	ax8.plot(data2410[0],data2410[1],'green--')
	ax9.plot(data2412[0],data2412[1],'red--')
	ax10.plot(data2414[0],data2414[1],'purple--')

	ax11.plot(data246[0],data246[1],'blue-')
	ax12.plot(data248[0],data248[1],'orange-')
	ax13.plot(data2410[0],data2410[1],'green-')
	ax14.plot(data2412[0],data2412[1],'red-')
	ax15.plot(data2414[0],data2414[1],'purple-')
	plotter.show()

	
import matplotlib.pyplot as plotter
import os		

def plotData(idx, Model_Number, Speed, TIME_AXIS, RESULT1, RESULT2):
	fig, ax1 = plotter.subplots()
	ax2 = ax1.twinx()
	ax1.plot(TIME_AXIS, RESULT1, linewidth = 1)
	ax2.plot(TIME_AXIS, RESULT2, linewidth = 1, color = "orange")
	plotter.title('Model: %s, Speed: %d' % (Model_Number, Speed))
	plotter.xlabel("Time")
	ax1.set_ylabel("Volts")
	ax1.set_ylim([-60,60])
	ax2.set_ylabel("Amps")
	ax2.set_ylim([-2,2])

	#plotter.legend()
	plotter.margins(0)
	plotter.grid('True')
	
	filepath = '/home/pi/Desktop/%s/' % Model_Number 
	if not os.path.exists(filepath):
		os.makedirs(filepath)
	
	filename = str(Model_Number) + "/" + str(Model_Number) + "_" + str(idx)
	plotter.savefig('/home/pi/Desktop/%s.png' % filename, dpi=300)
	plotter.clf()
	plotter.close()
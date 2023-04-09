import os
	
def writeheader(model_number, test_id, label):
	filepath = '/home/pi/Desktop/%s_%s/' % (model_number, test_id)
	csvfilepath = '/home/pi/Desktop/%s_%s/%s_Summary.csv' % (model_number, test_id,model_number)

	if not os.path.exists(filepath):
		os.makedirs(filepath)
	
	with open(csvfilepath, "w+") as file:
		if os.stat(csvfilepath).st_size == 0:
			file.write(str(label)[1:-1]+'\n')
	file.close()
	
def writedata(model_number, test_id, data):
	csvfilepath = '/home/pi/Desktop/%s_%s/%s_Summary.csv' % (model_number, test_id, model_number)
	with open(csvfilepath, "a") as file:
		file.write(str(data)[1:-1]+'\n')
	file.close()
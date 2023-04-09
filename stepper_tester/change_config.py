
def updateMS(microstep): # looping through the file
	line_idx = identifyLine('microsteps')
	file = open("/home/pi/printer_data/config/printer.cfg", "r")

	replaced_content = ""
	i = 0
	#print(line_idx)

	for line in file:
		line = line.strip()
    	# replacing the text if the line number is reached
		if (i == line_idx):
			new_line = "microsteps:%d" %microstep
			#print(new_line)
		else:
			new_line = line
		
		# concatenate the new string and add an end-line break
		replaced_content = replaced_content + new_line + "\n"
		
		# Increase loop counter
		i = i + 1

	# close the file
	file.close()
	
	# Open file in write mode
	write_file = open("/home/pi/printer_data/config/printer.cfg", "w")
	
	# overwriting the old file contents with the new/replaced content
	write_file.write(replaced_content)
	
	# close the file
	write_file.close()
	
def identifyLine(ID):
	file = open("/home/pi/printer_data/config/printer.cfg", "r")
	lines = file.readlines()
	for row in lines:
		word = ID
		if row.find(word) != -1:
			line_number = lines.index(row)
			file.close()
			return line_number
import serial

def restart():
	ser = serial.Serial("/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
	ser.write(str.encode("FIRMWARE_RESTART\n"))
	#print("Klipper Restarted")
	ser.close()
	
def current(amps):
	ser = serial.Serial("/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
	current_command = "SET_TMC_CURRENT STEPPER=stepper_M1 CURRENT=" + str(amps) + "\n"
	ser.write(str.encode(current_command))
	#print("Klipper Current Set")
	ser.close()

	
def move(time, speed, acceleration):
	ser = serial.Serial("/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
	distance = time * speed - (speed * speed / acceleration)
	move_command = "MANUAL_STEPPER SET_POSITION=0 STEPPER=stepper_M1 ENABLE=1 SPEED=" + str(speed) + " ACCEL=" + str(acceleration) + " MOVE=" + str(distance) + "\n"
	ser.write(str.encode(move_command))
	#print("Klipper Move Sent")
	ser.close()

	

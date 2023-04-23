import serial
import io
import string

def restart():
	ser = serial.Serial("/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
	ser.write(str.encode("FIRMWARE_RESTART\n"))
	ser.close()
	
def current(amps):
	ser = serial.Serial("/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
	current_command = "SET_TMC_CURRENT STEPPER=stepper_M3 CURRENT=" + str(amps) + "\n"
	ser.write(str.encode(current_command))
	print(f'      Set TMC Current: {amps}A')
	ser.close()

def move(time, speed, acceleration):
	ser = serial.Serial("/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
	distance = time * speed - (speed * speed / acceleration)
	move_command = "MANUAL_STEPPER SET_POSITION=0 STEPPER=stepper_M3 ENABLE=1 \
		SPEED=" + str(speed) + " ACCEL=" + str(acceleration) + " MOVE=" + str(distance) + "\n"
	ser.write(str.encode(move_command))
	ser.close()

def readtemp():
	ser = serial.Serial("/home/pi/printer_data/comms/klippy.serial", baudrate=250000, timeout=1)
	sio = io.TextIOWrapper(io.BufferedRWPair(ser,ser))
	ser.write(str.encode("M105\n"))
	sio.flush()
	temps_raw = sio.readline()
	temps_raw = temps_raw.split()
	temps = []
	for x in range(len(temps_raw)):
		for i in range(len(string.ascii_uppercase)):
			if(temps_raw[x][0] == string.ascii_uppercase[i]):
				temps.append(float(temps_raw[x][2:]))
	ser.close()
	temps = tuple(temps)
	return temps
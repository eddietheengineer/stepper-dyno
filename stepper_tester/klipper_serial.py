#Klipper Serial Communicator
import serial
import io
import string
import re
from dataclasses import dataclass

@dataclass
class temperaturedata:
    rpitemp: float
    drivertemp: float
    steppertemp: float

def restart():
    ser = serial.Serial(
        "/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
    ser.write(str.encode("FIRMWARE_RESTART\n"))
    print('      Klipper Restarted')
    ser.close()


def current(amps):
    ser = serial.Serial(
        "/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
    current_command = "SET_TMC_CURRENT STEPPER=stepper_M3 CURRENT=" + \
        str(amps) + "\n"
    ser.write(str.encode(current_command))
    print(f'      Set TMC Current: {amps}A')
    ser.close()


def move(time, speed, acceleration):
    ser = serial.Serial(
        "/home/pi/printer_data/comms/klippy.serial", baudrate=250000)
    distance = time * speed - (speed * speed / acceleration)
    move_command = "MANUAL_STEPPER SET_POSITION=0 STEPPER=stepper_M3 ENABLE=1 \
        SPEED=" + str(speed) + " ACCEL=" + str(acceleration) + " MOVE=" + str(distance) + "\n"
    ser.write(str.encode(move_command))
    ser.close()


def readtemp():
    ser = serial.Serial(
        "/home/pi/printer_data/comms/klippy.serial", baudrate=250000, timeout=1)
    sio = io.TextIOWrapper(io.BufferedRWPair(ser, ser))
    ser.write(str.encode("M105\n"))
    sio.flush()
    temps_raw = sio.readline()
    temps_split = temps_raw.split()

    # All measured temps have a uppercase A-Z character in the first position
    temps = [re.findall("\d+\.\d+", value)[0]
             for value in temps_split if value[0] in string.ascii_uppercase]
    ser.close()
    temperaturedata.rpitemp = float(temps[0])
    temperaturedata.drivertemp = float(temps[1])
    temperaturedata.steppertemp = float(temps[2])
    return temperaturedata

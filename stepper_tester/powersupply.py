import time
from riden import Riden
r = Riden(port="/dev/serial/by-id/usb-1a86_USB_Serial-if00-port0", baudrate=115200, address=1)
	
def scan():
	return (r.get_v_set(), r.get_v_out(), r.get_i_out(), r.get_p_out())
	
def voltage_setting(voltage):
	r.set_v_set(voltage)
	r.set_output(1)
	
def initialize(voltage):
	r.set_v_set(voltage)
	r.set_i_set(6)
	r.set_output(1)
	print("Riden Initialized")

def close():
	r.set_output(0)
	print("Rident Off")
import serial
import platform
from time import sleep
if platform.system() == "Linux" :
  port="/dev/ttyUSB0"
elif platform.system() == "Windows" :
  port="COM3"
ser = serial.Serial(port,9600,timeout=1)	#9600 is default
print ser	#display interface settings

while 1:
	code=raw_input("Code a envoyer : ")
	ser.write(code)


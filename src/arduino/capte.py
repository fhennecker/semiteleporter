import datetime, time
import serial
import platform
import numpy
import cv2

# arduino commands
LEDS_OFF="0"
LED1_ON="1"
LED2_ON="2"
STEP="3"
CHANGE_DIR="4"
POWER_OFF="9"
# stepper params
resolution=4096 # number of half-steps per revolution

# arduino initialization
if platform.system() == "Linux" :
  port="/dev/ttyUSB0"
elif platform.system() == "Windows" :
  port="COM3"
ser = serial.Serial(port,9600,timeout=1)	#9600 is default
print ser	#display interface settings

# camera initialization
cap=cv2.VideoCapture(0)
print "opencv",cv2.__version__

print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
for i in range (1,resolution):
	ser.write(LED1_ON)
	ret1, frame1 = cap.read()	# Capture a frame
	ser.write(LEDS_OFF)
	ser.write(LED2_ON)
	ret1, frame1 = cap.read()	# Capture a frame
	ser.write(LEDS_OFF)
	ret2, frame2 = cap.read()	# Capture a frame

	# Our operations on the frames come here
	
	ser.write(STEP)

print datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d %H:%M:%S')
ser.write(POWER_OFF)
cap.release()
# cv2.destroyAllWindows()

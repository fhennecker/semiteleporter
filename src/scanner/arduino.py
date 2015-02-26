import logging
import serial
import numpy as np

class Arduino:
    def __init__(self, port, isActive=True):
        """ Create a new Arduino object
        port = the serial port for the arduino
        """
        logging.debug("Create Arduino @ port %s" % (port))
        self.isActive = isActive
        if(isActive):
            try:
                self.serialPort = serial.Serial(port, 115200)
                time.sleep(2)
                self.command('P')
                logging.debug("Handshaking with Arduino...")
            except:
                logging.warning("\033[93m No arduino connected / bad serial port.. \033[0m")

    def command(self, cmd):
        #FIXME why arduino fails to response sometimes ?
        response = ''
        if(self.isActive):
            try:
                self.serialPort.write(cmd)
                while(response == ''):
                    response = self.serialPort.read(3)
            except:
                logging.exception("\033[93m Impossible to send the command to the arduino.. \033[0m")

        return response

    def debugMode(self):
        cmd = raw_input('command : ')
        while(cmd not in ('q','quit','e','exit')):
            response = self.command(cmd)
            print("Response : %s" %response)
            cmd = raw_input('command : ')


class Laser:
    def __init__(self, pin, position, yAngle, arduino):
        """ Create a new Laser object
        pin      = number of the pin connected to the arduino
        position = [X, Y, Z], laser position
        yAngle   = angle of the laser plane with YZ plane in radians (left=positive)
        arduino  = the arduino interface
        """

        logging.debug("Create laser @ %s, yAngle=%.2f, pin=%s" % (position, yAngle, pin))

        self.pin      = pin
        self.position = np.array(position, dtype=np.float32)
        self.yAngle   = yAngle
        self.arduino  = arduino
        self.v1       = np.array([0,1,0], dtype=np.float32)
        self.v2       = np.array([-np.sin(self.yAngle), 0, np.cos(self.yAngle)], dtype=np.float32)

    def switch(self, switchOn):
        if(switchOn):
            self.arduino.command(self.pin.upper())
            logging.info('Switching laser on pin %s %s' %(self.pin, 'ON'))
        else:
            self.arduino.command(self.pin.lower())
            logging.info('Switching laser on pin %s %s' %(self.pin, 'OFF'))


class TurnTable:
    def __init__(self, position, diameter, nSteps, arduino):
        """ Create a new TurnTable object
        position = [X, Y, Z], turntable position
        diameter = <diameter>, turntable diameter
        nSteps   = number of steps for a full turn
        arduino  = the arduino interface
        """

        logging.debug("Create turntable @ %s, diameter = %.2f" % (position, diameter))

        self.position  = np.array(position, dtype=np.float32)
        self.diameter  = diameter
        self.nSteps    = int(nSteps)
        self.arduino   = arduino
        self.stepAngle = 2.0*np.pi/nSteps

    def getRotationMatrix(self, step):
        angle = self.stepAngle*step
        rotationMatrix = np.matrix([[np.cos(angle), 0, -np.sin(angle)],
                                    [0            , 1,              0],
                                    [np.sin(angle), 0,  np.cos(angle)]])
        return rotationMatrix
        
    def rotate(self, step=1):
        logging.info('Rotating the turntable')
        self.arduino.command('T')

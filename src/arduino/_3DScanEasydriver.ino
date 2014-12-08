/*
  3DScan
  This driver controls a easydriver
  H.P.
  Commands are :
  0 : Diodes 1 & 2 OFF
  1 : Diode 1 ON
  2 : Diode 2 ON
  3 : one step
  4 : change direction (no step)
  5 : 1024 steps for a test
  9 : power off
 */
int dirPin = 2;
int stepperPin = 3;
int diode1 = 12;
int diode2 = 13;
int cmd=0;
boolean dir = true;

void setup() {
 Serial.begin(9600);
 pinMode(dirPin, OUTPUT);
 digitalWrite(dirPin,dir);
 pinMode(stepperPin, OUTPUT);
 pinMode(diode1, OUTPUT);
 pinMode(diode2, OUTPUT);
}

void loop() {
  if (Serial.available()>0)
  { 
    cmd=int(Serial.read())-48;
  //cmd is an integer 0-9
    Serial.println(cmd);
  //feedback a trace of the command
  switch(cmd){
    case 9:
    case 0:
    // lasers OFF
      digitalWrite(diode1, LOW);
      digitalWrite(diode2, LOW);
      break;
    case 1:
    // laser 1 ON
      digitalWrite(diode1, HIGH);
      break;
    case 2:
    // laser 2 ON
      digitalWrite(diode2, HIGH);
      break;      
    case 4:
    // change direction
      dir=! dir;
      digitalWrite(dirPin,dir);
      break;
     case 5:
    // 1024 steps for a test
      for (int i=0;i<1024;i++) {
        step();
        delay(10); }
      break;
    
    default:
      step();
  }
  }      
}

void step() {
  //implements a step within a 8 steps sequence (default)
  digitalWrite(stepperPin,LOW);
  digitalWrite(stepperPin,HIGH);
}

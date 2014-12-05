/*
  3DScan
  This driver controls a easydriver
  H.P.
  Commands are :
  0 : Diode OFF
  1 : Diode ON
  2 : one step
  4 : change direction (no step)
  5 : 1024 steps for a test
 */
int dirPin = 2;
int stepperPin = 3;
int cmd=0;
boolean dir = true;

void setup() {
 Serial.begin(9600);
 pinMode(dirPin, OUTPUT);
 digitalWrite(dirPin,dir);
 pinMode(stepperPin, OUTPUT);
 pinMode(13, OUTPUT);
// PIN 13 commands the lasers 
}

void loop() {
  if (Serial.available()>0)
  { 
    cmd=int(Serial.read())-48;
  //cmd is an integer 0-9
    Serial.println(cmd);
  //feedback a trace of the command
  switch(cmd){
    case 0:
    // lasers OFF
      digitalWrite(13, LOW);
      break;
    case 1:
    // lasers ON
      digitalWrite(13, HIGH);
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
      
    case 9:
    // power off
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
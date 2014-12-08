/*
  3DScan
  This driver controls a ULN2003 driver
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
int Pin0 = 8;
int Pin1 = 9;
int Pin2 = 10;
int Pin3 = 11;
int diode1 = 12;
int diode2 = 13;
int _step = 0;
int cmd=0;
boolean dir = true;

void setup() {
 Serial.begin(9600);
 pinMode(Pin0, OUTPUT);  
 pinMode(Pin1, OUTPUT);  
 pinMode(Pin2, OUTPUT);  
 pinMode(Pin3, OUTPUT);
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
    // power off
     digitalWrite(Pin0, LOW);  
     digitalWrite(Pin1, LOW);
     digitalWrite(Pin2, LOW);
     digitalWrite(Pin3, LOW);
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
  //implements a step within a 8 steps sequence
   switch(_step){
   case 0:
     digitalWrite(Pin0, LOW);  
     digitalWrite(Pin1, LOW);
     digitalWrite(Pin2, LOW);
     digitalWrite(Pin3, HIGH);
   break;  
   case 1:
     digitalWrite(Pin0, LOW);  
     digitalWrite(Pin1, LOW);
     digitalWrite(Pin2, HIGH);
     digitalWrite(Pin3, HIGH);
   break;  
   case 2:
     digitalWrite(Pin0, LOW);  
     digitalWrite(Pin1, LOW);
     digitalWrite(Pin2, HIGH);
     digitalWrite(Pin3, LOW);
   break;  
   case 3:
     digitalWrite(Pin0, LOW);  
     digitalWrite(Pin1, HIGH);
     digitalWrite(Pin2, HIGH);
     digitalWrite(Pin3, LOW);
   break;  
   case 4:
     digitalWrite(Pin0, LOW);  
     digitalWrite(Pin1, HIGH);
     digitalWrite(Pin2, LOW);
     digitalWrite(Pin3, LOW);
   break;  
   case 5:
     digitalWrite(Pin0, HIGH);  
     digitalWrite(Pin1, HIGH);
     digitalWrite(Pin2, LOW);
     digitalWrite(Pin3, LOW);
   break;  
     case 6:
     digitalWrite(Pin0, HIGH);  
     digitalWrite(Pin1, LOW);
     digitalWrite(Pin2, LOW);
     digitalWrite(Pin3, LOW);
   break;  
   case 7:
     digitalWrite(Pin0, HIGH);  
     digitalWrite(Pin1, LOW);
     digitalWrite(Pin2, LOW);
     digitalWrite(Pin3, HIGH);
   break;  
   default:
     digitalWrite(Pin0, LOW);  
     digitalWrite(Pin1, LOW);
     digitalWrite(Pin2, LOW);
     digitalWrite(Pin3, LOW);
   break;  
 }
 if(dir){
   _step++;
 }else{
   _step--;
 }
 if(_step>7){
   _step=0;
 }
 if(_step<0){
   _step=7;
 }
}


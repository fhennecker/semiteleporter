/*
  3DScan
  This driver controls a easydriver
  H.P.
  Commands are :
  r/R: light right laser
  l/L: light left laser
  t/T: turn
  0: shut off both lasers
  b/B: light both lasers
  p/P: put power on
  m/M: put power off
 */

/* Pinout */
static const int dirPin = 2;
static const int stepPin = 3;
static const int laserLeftPin = 12;
static const int laserRightPin = 11;
static const int powerPin = 4;

/* Delay, in milliseconds, to ensure laser state totally changed (on/off time) */
static const int lightDelay = 1;

/* Delay, in microseconds, between each motor half step */
static const int stepDelayMax = 2000;
static const int stepDelayMin = 1500;
static int stepDelay;

/* Delay, in milliseconds to wait after motor turn (plate stabilization) */
static const int afterTurnDelay = 150;

/* Number of steps for a complete rotation */
static const int totalSteps = 8000;

/* Change lasers state */
void laser(int laser_pin, bool value){
  digitalWrite(laser_pin, value ? HIGH : LOW);
  delay(lightDelay);
}

void power(bool on){
  digitalWrite(powerPin, on ? HIGH : LOW);
}

/* Turn platform */
void turn(int n_steps=100){
  int half = n_steps/2;
  int increment = (stepDelayMax - stepDelayMin) / half;
  stepDelay = stepDelayMax;

  for (; n_steps>0; n_steps--){
    digitalWrite(stepPin, HIGH);
    delayMicroseconds(stepDelay);
    digitalWrite(stepPin, LOW);
    delayMicroseconds(stepDelay);
    if (n_steps > half)
      stepDelay -= increment;
    else
      stepDelay += increment;
  }
  delay(afterTurnDelay);
}

void setup() {
  Serial.begin(115200);
  pinMode(dirPin, OUTPUT);
  digitalWrite(dirPin, HIGH);
  pinMode(stepPin, OUTPUT);
  digitalWrite(stepPin, LOW);
  pinMode(laserLeftPin, OUTPUT);
  pinMode(laserRightPin, OUTPUT);
  pinMode(powerPin, OUTPUT);
  digitalWrite(powerPin, LOW);
  laser(false, false);
}

char cmd = 0;
bool ok = true;
void loop() {
  if (Serial.available() > 0){
    ok = true;
    cmd = Serial.read();
    switch (cmd) {
      case '0':
        laser(laserLeftPin, false);
        laser(laserRightPin, false);
        break;

      case 'b':
      case 'B':
        laser(laserLeftPin, true);
        laser(laserRightPin, true);
        break;

      case 'l':
        laser(laserLeftPin, false);
        break;
      case 'L':
        laser(laserLeftPin, true);
        break;

      case 'r':
        laser(laserRightPin, false);
        break;
      case 'R':
        laser(laserRightPin, true);
        break;

      case 't':
      case 'T':
        turn();
        break;

      case 'p':
      case 'P':
        power(true);
        break;

      case 'm':
      case 'M':
        power(false);
        break;

      /* Unknow command*/
      default: 
        ok = false;
    }
    /* Echo back if command suceeded */
    if (ok) 
      Serial.println(cmd);
  }      
}

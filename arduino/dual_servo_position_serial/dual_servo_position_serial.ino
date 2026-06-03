#include <Servo.h>

const int PAN_PIN = 9;
const int TILT_PIN = 10;

const int PAN_MIN = 0;
const int PAN_MAX = 180;
const int TILT_MIN = 10;
const int TILT_MAX = 90;

const int PAN_CENTER = 90;
const int TILT_CENTER = 45;

const int STEP_DEGREES = 1;
const unsigned long STEP_DELAY_MS = 15;

Servo panServo;
Servo tiltServo;

int panNow = PAN_CENTER;
int tiltNow = TILT_CENTER;
int panTarget = PAN_CENTER;
int tiltTarget = TILT_CENTER;
unsigned long lastStepAt = 0;

int clampAngle(int value, int minValue, int maxValue) {
  if (value < minValue) {
    return minValue;
  }
  if (value > maxValue) {
    return maxValue;
  }
  return value;
}

int stepToward(int current, int target) {
  if (current < target) {
    return min(current + STEP_DEGREES, target);
  }
  if (current > target) {
    return max(current - STEP_DEGREES, target);
  }
  return current;
}

void setTargets(int pan, int tilt) {
  panTarget = clampAngle(pan, PAN_MIN, PAN_MAX);
  tiltTarget = clampAngle(tilt, TILT_MIN, TILT_MAX);

  Serial.print("TARGET ");
  Serial.print(panTarget);
  Serial.print(",");
  Serial.println(tiltTarget);
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "CENTER") {
    setTargets(PAN_CENTER, TILT_CENTER);
    return;
  }

  int commaIndex = cmd.indexOf(',');
  if (commaIndex < 0) {
    Serial.println("ERR USE pan,tilt OR CENTER");
    return;
  }

  int pan = cmd.substring(0, commaIndex).toInt();
  int tilt = cmd.substring(commaIndex + 1).toInt();
  setTargets(pan, tilt);
}

void setup() {
  Serial.begin(115200);
  panServo.attach(PAN_PIN);
  tiltServo.attach(TILT_PIN);

  panServo.write(panNow);
  tiltServo.write(tiltNow);

  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
  }

  unsigned long now = millis();
  if (now - lastStepAt < STEP_DELAY_MS) {
    return;
  }
  lastStepAt = now;

  panNow = stepToward(panNow, panTarget);
  tiltNow = stepToward(tiltNow, tiltTarget);

  panServo.write(panNow);
  tiltServo.write(tiltNow);
}

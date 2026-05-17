#include <Servo.h>

const int SERVO1_PIN = 9;
const int SERVO2_PIN = 10;
const int MIN_ANGLE = 10;
const int MAX_ANGLE = 90;
const int STEP_DEGREES = 1;
const unsigned long STEP_DELAY_MS = 20;  // medium speed
const int SWEEP_CYCLES = 5;              // 10->90->10 counts as one cycle

Servo servo1;
Servo servo2;

bool sweeping = false;
int angle = MIN_ANGLE;
int direction = STEP_DEGREES;
int completedCycles = 0;
unsigned long lastStepAt = 0;

void writeBoth(int degrees) {
  servo1.write(degrees);
  servo2.write(degrees);
}

void startSweep() {
  sweeping = true;
  angle = MIN_ANGLE;
  direction = STEP_DEGREES;
  completedCycles = 0;
  lastStepAt = 0;
  writeBoth(angle);
  Serial.println("SWEEPING_BOTH_5X");
}

void stopSweep() {
  sweeping = false;
  writeBoth(90);
  Serial.println("STOPPED");
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "SWEEP" || cmd == "RUN") {
    startSweep();
  } else if (cmd == "STOP") {
    stopSweep();
  }
}

void setup() {
  Serial.begin(115200);
  servo1.attach(SERVO1_PIN);
  servo2.attach(SERVO2_PIN);
  writeBoth(90);
  Serial.println("READY");
}

void loop() {
  while (Serial.available() > 0) {
    String cmd = Serial.readStringUntil('\n');
    handleCommand(cmd);
  }

  if (!sweeping) {
    return;
  }

  unsigned long now = millis();
  if (now - lastStepAt < STEP_DELAY_MS) {
    return;
  }
  lastStepAt = now;

  writeBoth(angle);
  angle += direction;

  if (angle >= MAX_ANGLE) {
    angle = MAX_ANGLE;
    direction = -STEP_DEGREES;
  } else if (angle <= MIN_ANGLE) {
    angle = MIN_ANGLE;
    direction = STEP_DEGREES;
    completedCycles += 1;
    if (completedCycles >= SWEEP_CYCLES) {
      stopSweep();
    }
  }
}

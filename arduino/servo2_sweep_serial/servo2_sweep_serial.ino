#include <Servo.h>

const int SERVO2_PIN = 10;
const int MIN_ANGLE = 45;
const int MAX_ANGLE = 135;
const int STEP_DEGREES = 1;
const unsigned long STEP_DELAY_MS = 15;

Servo servo2;
bool sweeping = false;
int angle = MIN_ANGLE;
int direction = STEP_DEGREES;
unsigned long lastStepAt = 0;

void setup() {
  Serial.begin(115200);
  servo2.attach(SERVO2_PIN);
  servo2.write(90);
  Serial.println("READY");
}

void handleCommand(String cmd) {
  cmd.trim();
  cmd.toUpperCase();

  if (cmd == "SWEEP") {
    sweeping = true;
    Serial.println("SWEEPING");
  } else if (cmd == "STOP") {
    sweeping = false;
    servo2.write(90);
    Serial.println("STOPPED");
  }
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

  servo2.write(angle);
  angle += direction;

  if (angle >= MAX_ANGLE) {
    angle = MAX_ANGLE;
    direction = -STEP_DEGREES;
  } else if (angle <= MIN_ANGLE) {
    angle = MIN_ANGLE;
    direction = STEP_DEGREES;
  }
}

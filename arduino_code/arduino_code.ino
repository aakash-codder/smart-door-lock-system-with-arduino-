#include <Servo.h>

Servo myservo;

void setup() {
  myservo.attach(3);     // Servo on pin 3
  Serial.begin(9600);    // Communication with Python
  myservo.write(0);      // Start at 0 degrees
}

void loop() {
  if (Serial.available()) {
    char cmd = Serial.read();

    if (cmd == 'a') {     // Received from Python
      myservo.write(85);  // Rotate to 70 degrees
      delay(5000);
      myservo.write(0);   // Move back to 0
    }
  }
}

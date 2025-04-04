// This file is taking analog input from mq3 sesnor every 2 seconds and is connected to the raspberry pi for serial communication

const int sensorPin = A0; // Analog input pin for 

void setup() {
  Serial.begin(115200);
}

void loop() {
  int sensorValue = analogRead(sensorPin);
  Serial.print("Sensor Value: ");
  Serial.println(sensorValue);
  delay(2000); // Delay between readings
}

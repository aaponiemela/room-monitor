#include <Arduino_BHY2.h>

Sensor temperature(SENSOR_ID_TEMP);
Sensor humidity(SENSOR_ID_HUM);
Sensor pressure(SENSOR_ID_BARO);

const unsigned long SEND_INTERVAL_MS = 1000;
unsigned long lastSendTime = 0;

void setup() {
  Serial.begin(115200);

  // Wait for the computer to open the serial connection.
  while (!Serial) {
  }

  BHY2.begin();

  temperature.begin();
  humidity.begin();
  pressure.begin();
}

void loop() {
  // Keep processing sensor data without blocking the loop.
  BHY2.update();

  const unsigned long now = millis();

  if (now - lastSendTime < SEND_INTERVAL_MS) {
    return;
  }

  // Send only after every sensor has provided new data.
  if (!temperature.dataAvailable() ||
      !humidity.dataAvailable() ||
      !pressure.dataAvailable()) {
    return;
  }

  Serial.print("{\"uptime_ms\":");
  Serial.print(now);

  Serial.print(",\"temperature_c\":");
  Serial.print(temperature.value(), 2);

  Serial.print(",\"humidity_pct\":");
  Serial.print(humidity.value(), 2);

  Serial.print(",\"pressure_hpa\":");
  Serial.print(pressure.value(), 2);

  Serial.println("}");

  temperature.clearDataAvailFlag();
  humidity.clearDataAvailFlag();
  pressure.clearDataAvailFlag();

  lastSendTime = now;
}
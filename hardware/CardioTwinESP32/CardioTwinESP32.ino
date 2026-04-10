#include <Arduino.h>
#include <Wire.h>
#include <WiFi.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include "MAX30105.h"
#include "spo2_algorithm.h"
#include <math.h>

MAX30105 particleSensor;

// --- NETWORK CONFIG ---
// Replace these before flashing.
const char *WIFI_SSID = "HACKATHON_WIFI";
const char *WIFI_PASS = "HACKATHON_PASSWORD";
const char *API_BASE_URL = "https://cardiotwin-jqrct.ondigitalocean.app";

// Backend endpoints
const char *SESSION_START_PATH = "/api/session/start";
const char *READING_PATH = "/api/reading";

// Session sent to backend. Keep stable for one live run.
const char *SESSION_ID = "demo";

// --- PIN DEFINITIONS ---
#define ADC_PIN 34
#define I2C_SDA 21
#define I2C_SCL 22
#define GREEN_LED_PIN 26
#define RED_LED_PIN 27
#define BUZZER_PIN 25

// --- SENSOR/LOOP CONFIG ---
const unsigned long SEND_INTERVAL_MS = 2000;
const uint32_t FINGER_THRESHOLD = 50000;

// --- THERMISTOR CONFIG ---
const float SERIES_RESISTOR = 10000.0;
const float NOMINAL_RESISTANCE = 10000.0;
const float NOMINAL_TEMPERATURE = 25.0;
const float BETA_COEFFICIENT = 3950.0;
const float CALIBRATION_OFFSET = 4.0;

// --- FILTERING & BUFFER SETTINGS ---
#define FILTER_SIZE 6
int32_t bpmAvg[FILTER_SIZE];
int avgIdx = 0;

float rrIntervals[12];
int rrCount = 0;

uint32_t irBuffer[100];
uint32_t redBuffer[100];
int32_t spo2, heartRate;
int8_t validSPO2, validHeartRate;

unsigned long lastPostMs = 0;

float clampFloat(float value, float minValue, float maxValue) {
  if (value < minValue) return minValue;
  if (value > maxValue) return maxValue;
  return value;
}

void beep(uint16_t frequency, uint16_t durationMs) {
  tone(BUZZER_PIN, frequency, durationMs);
}

void blinkLed(uint8_t pin, uint16_t onMs, uint16_t offMs) {
  digitalWrite(pin, HIGH);
  delay(onMs);
  digitalWrite(pin, LOW);
  delay(offMs);
}

void showNoFingerState() {
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, HIGH);
}

void showHealthySendState() {
  digitalWrite(RED_LED_PIN, LOW);
  blinkLed(GREEN_LED_PIN, 100, 20);
}

void showSendFailState() {
  digitalWrite(GREEN_LED_PIN, LOW);
  blinkLed(RED_LED_PIN, 120, 60);
  blinkLed(RED_LED_PIN, 120, 20);
  beep(400, 100);
}

void showAlertState() {
  digitalWrite(GREEN_LED_PIN, LOW);
  for (int i = 0; i < 3; i++) {
    digitalWrite(RED_LED_PIN, HIGH);
    beep(800, 180);
    delay(220);
    digitalWrite(RED_LED_PIN, LOW);
    delay(100);
  }
}

void ensureWiFiConnected() {
  if (WiFi.status() == WL_CONNECTED) {
    return;
  }

  Serial.print("[WiFi] Connecting to ");
  Serial.println(WIFI_SSID);

  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);

  const unsigned long start = millis();
  while (WiFi.status() != WL_CONNECTED && (millis() - start) < 15000) {
    delay(300);
    Serial.print(".");
  }
  Serial.println();

  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("[WiFi] Connected. IP: ");
    Serial.println(WiFi.localIP());
    beep(1000, 60);
    delay(50);
    beep(1200, 60);
  } else {
    Serial.println("[WiFi] Connection failed.");
    showSendFailState();
  }
}

bool postJson(const String &url, const String &body, int &httpCode, String &responseBody) {
  HTTPClient http;
  http.begin(url);
  http.addHeader("Content-Type", "application/json");
  http.setTimeout(5000);

  httpCode = http.POST(body);
  if (httpCode > 0) {
    responseBody = http.getString();
  } else {
    responseBody = "";
  }

  http.end();
  return httpCode > 0 && httpCode < 300;
}

void startSessionOnce() {
  if (WiFi.status() != WL_CONNECTED) {
    return;
  }

  StaticJsonDocument<256> doc;
  doc["session_id"] = SESSION_ID;

  String payload;
  serializeJson(doc, payload);

  int code = 0;
  String response;
  const String url = String(API_BASE_URL) + SESSION_START_PATH;

  bool ok = postJson(url, payload, code, response);
  Serial.print("[Session] POST ");
  Serial.print(url);
  Serial.print(" -> ");
  Serial.println(code);

  if (ok) {
    Serial.print("[Session] Response: ");
    Serial.println(response);
  } else {
    Serial.print("[Session] Failed. Body: ");
    Serial.println(response);
  }
}

float readSkinTemp() {
  float reading = 0.0;
  for (int i = 0; i < 20; i++) {
    reading += analogRead(ADC_PIN);
    delay(2);
  }
  reading /= 20.0;

  if (reading <= 0 || reading >= 4095) {
    return NAN;
  }

  float resistance = SERIES_RESISTOR * (4095.0 / reading - 1.0);

  float temp = resistance / NOMINAL_RESISTANCE;
  temp = log(temp);
  temp /= BETA_COEFFICIENT;
  temp += 1.0 / (NOMINAL_TEMPERATURE + 273.15);
  temp = 1.0 / temp;
  float finalCelsius = temp - 273.15 + CALIBRATION_OFFSET;

  return finalCelsius;
}

float calculateSDNN(float data[], int n) {
  if (n < 2) return 0.0;

  float sum = 0.0;
  float varSum = 0.0;
  for (int i = 0; i < n; i++) sum += data[i];
  float mean = sum / n;
  for (int i = 0; i < n; i++) varSum += pow(data[i] - mean, 2);
  return sqrt(varSum / n);
}

bool isValidForBackend(float bpm, float hrv, float spo2Pct, float tempC) {
  if (isnan(bpm) || isnan(hrv) || isnan(spo2Pct) || isnan(tempC)) {
    return false;
  }

  // Match backend validator bounds in ai_engine/validation.py
  if (bpm < 30.0 || bpm > 220.0) return false;
  if (hrv < 0.0 || hrv > 200.0) return false;
  if (spo2Pct < 70.0 || spo2Pct > 100.0) return false;
  if (tempC < 30.0 || tempC > 42.0) return false;

  return true;
}

void sendReading(float bpm, float hrv, float spo2Pct, float tempC) {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("[API] Skip send: WiFi not connected.");
    showSendFailState();
    return;
  }

  StaticJsonDocument<512> doc;
  doc["session_id"] = SESSION_ID;
  doc["bpm"] = bpm;
  doc["hrv"] = hrv;
  doc["spo2"] = spo2Pct;
  doc["temperature"] = tempC;
  doc["timestamp"] = millis();
  doc["source"] = "hardware";

  String payload;
  serializeJson(doc, payload);

  int code = 0;
  String response;
  const String url = String(API_BASE_URL) + READING_PATH;
  bool ok = postJson(url, payload, code, response);

  Serial.print("[API] POST /api/reading -> ");
  Serial.println(code);

  if (!ok) {
    Serial.print("[API] Error response: ");
    Serial.println(response);
    showSendFailState();
    return;
  }

  DynamicJsonDocument respDoc(1024);
  DeserializationError err = deserializeJson(respDoc, response);
  if (err) {
    Serial.print("[API] JSON parse failed: ");
    Serial.println(err.c_str());
    showSendFailState();
    return;
  }

  const char *status = respDoc["status"] | "unknown";
  bool alert = respDoc["alert"] | false;

  Serial.print("[API] status=");
  Serial.print(status);

  if (strcmp(status, "calibrating") == 0) {
    int collected = respDoc["readings_collected"] | 0;
    int needed = respDoc["readings_needed"] | 0;
    Serial.print(" (");
    Serial.print(collected);
    Serial.print("/");
    Serial.print(needed);
    Serial.print(")");
  } else if (strcmp(status, "scored") == 0) {
    float score = respDoc["score"] | 0.0;
    const char *zone = respDoc["zone"] | "UNKNOWN";
    Serial.print(" score=");
    Serial.print(score, 1);
    Serial.print(" zone=");
    Serial.print(zone);
  } else if (strcmp(status, "retake_requested") == 0) {
    const char *msg = respDoc["message"] | "Retake requested";
    Serial.print(" message=");
    Serial.print(msg);
  }

  Serial.println();

  if (alert) {
    showAlertState();
  } else {
    showHealthySendState();
  }
}

void setup() {
  Serial.begin(115200);
  analogReadResolution(12);

  pinMode(GREEN_LED_PIN, OUTPUT);
  pinMode(RED_LED_PIN, OUTPUT);
  pinMode(BUZZER_PIN, OUTPUT);
  digitalWrite(GREEN_LED_PIN, LOW);
  digitalWrite(RED_LED_PIN, LOW);

  Wire.begin(I2C_SDA, I2C_SCL);
  delay(1000);

  if (!particleSensor.begin(Wire, 100000)) {
    Serial.println(">>> Sensor Error: Check SDA/SCL wiring. <<<");
    digitalWrite(RED_LED_PIN, HIGH);
    while (1) {
      beep(250, 250);
      delay(400);
    }
  }

  // High sample rate for HRV precision
  particleSensor.setup(70, 4, 2, 200, 411, 4096);

  // Seed filter with stable startup value.
  for (int i = 0; i < FILTER_SIZE; i++) bpmAvg[i] = 72;

  ensureWiFiConnected();
  startSessionOnce();

  Serial.println("SYSTEM INITIALIZED");
}

void loop() {
  ensureWiFiConnected();

  uint64_t irSum = 0;

  // 1) Collect samples from MAX30102
  for (byte i = 0; i < 100; i++) {
    while (!particleSensor.available()) {
      particleSensor.check();
    }
    redBuffer[i] = particleSensor.getRed();
    irBuffer[i] = particleSensor.getIR();
    irSum += irBuffer[i];
    particleSensor.nextSample();
  }

  const uint32_t avgIr = (uint32_t)(irSum / 100);
  if (avgIr < FINGER_THRESHOLD) {
    Serial.println("Searching... No finger detected.");
    showNoFingerState();
    delay(250);
    return;
  }

  // 2) Estimate heart rate + SpO2 from sampled windows
  maxim_heart_rate_and_oxygen_saturation(
      irBuffer,
      100,
      redBuffer,
      &spo2,
      &validSPO2,
      &heartRate,
      &validHeartRate);

  // 3) Read temperature from thermistor channel
  float skinTemp = readSkinTemp();

  if (!(validHeartRate && heartRate > 40 && heartRate < 175)) {
    Serial.print("Searching... [Current Temp: ");
    Serial.print(skinTemp, 1);
    Serial.println("C]");
    showNoFingerState();
    delay(200);
    return;
  }

  // 4) Smooth BPM
  bpmAvg[avgIdx % FILTER_SIZE] = heartRate;
  avgIdx++;

  long sum = 0;
  for (int i = 0; i < FILTER_SIZE; i++) sum += bpmAvg[i];
  float finalBPM = (float)sum / FILTER_SIZE;

  // 5) Derive HRV (SDNN from rolling RR intervals)
  float currentRR = 60000.0 / finalBPM;
  rrIntervals[rrCount % 12] = currentRR;
  rrCount++;
  float sdnn = calculateSDNN(rrIntervals, min(rrCount, 12));

  // 6) Use SPO2 output only if algorithm marks it valid
  float spo2Pct = validSPO2 ? (float)spo2 : NAN;

  // Clamp softly before backend validation checks.
  float safeTemp = clampFloat(skinTemp, 28.0, 45.0);

  Serial.print("BPM: ");
  Serial.print(finalBPM, 1);
  Serial.print(" | SpO2: ");
  if (isnan(spo2Pct)) {
    Serial.print("invalid");
  } else {
    Serial.print(spo2Pct, 1);
  }
  Serial.print("% | HRV: ");
  Serial.print(sdnn, 1);
  Serial.print("ms | Temp: ");
  Serial.print(safeTemp, 1);
  Serial.println("C");

  if (!isValidForBackend(finalBPM, sdnn, spo2Pct, safeTemp)) {
    Serial.println("[Validation] Skipping send: one or more values out of backend range.");
    showSendFailState();
    return;
  }

  const unsigned long now = millis();
  if (now - lastPostMs >= SEND_INTERVAL_MS) {
    lastPostMs = now;
    sendReading(finalBPM, sdnn, spo2Pct, safeTemp);
  }
}
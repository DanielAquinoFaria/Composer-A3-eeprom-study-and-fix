#include <Wire.h>
#include <stdlib.h>
#include <string.h>

// Arduino Uno R3 / ATmega328P. WP requires an external 10k pull-up to 5V.
const uint8_t WP_PIN = 7;
const uint8_t BLOCK = 30; // Wire: 32 bytes minus two address bytes.
char input[160];
uint8_t used = 0;
bool discard = false;
unsigned long lastByte = 0;

uint16_t crc16(const char *s) {
  uint16_t crc = 0xFFFF;
  while (*s) {
    crc ^= (uint16_t)(uint8_t)*s++ << 8;
    for (uint8_t i = 0; i < 8; i++)
      crc = (crc & 0x8000) ? (crc << 1) ^ 0x1021 : crc << 1;
  }
  return crc;
}

void reply(uint16_t id, const char *status, const char *value) {
  char out[120];
  snprintf(out, sizeof(out), "%u %s %s", id, status, value);
  uint16_t crc = crc16(out);
  Serial.print(out);
  Serial.print('*');
  char hex[5];
  snprintf(hex, sizeof(hex), "%04X", crc);
  Serial.println(hex);
}

bool number(const char *s, uint32_t limit, uint32_t &value) {
  if (!s || !*s) return false;
  value = 0;
  while (*s) {
    if (*s < '0' || *s > '9') return false;
    value = value * 10 + (*s++ - '0');
    if (value > limit) return false;
  }
  return true;
}

int nibble(char c) {
  if (c >= '0' && c <= '9') return c - '0';
  if (c >= 'A' && c <= 'F') return c - 'A' + 10;
  if (c >= 'a' && c <= 'f') return c - 'a' + 10;
  return -1;
}

bool readMemory(uint8_t dev, uint16_t addr, uint8_t n, uint8_t *data) {
  Wire.clearWireTimeoutFlag();
  Wire.beginTransmission(dev);
  Wire.write((uint8_t)(addr >> 8));
  Wire.write((uint8_t)addr);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(dev, n) != n || Wire.getWireTimeoutFlag()) return false;
  for (uint8_t i = 0; i < n; i++) data[i] = Wire.read();
  return true;
}

bool writeMemory(uint8_t dev, uint16_t addr, uint8_t n, uint8_t *data) {
  Wire.clearWireTimeoutFlag();
  digitalWrite(WP_PIN, LOW);
  Wire.beginTransmission(dev);
  Wire.write((uint8_t)(addr >> 8));
  Wire.write((uint8_t)addr);
  Wire.write(data, n);
  uint8_t result = Wire.endTransmission();
  // WP sampled at STOP; hold it low briefly beyond that edge.
  delayMicroseconds(10);
  digitalWrite(WP_PIN, HIGH);
  if (result != 0 || Wire.getWireTimeoutFlag()) return false;
  unsigned long start = millis();
  do {
    Wire.beginTransmission(dev);
    if (Wire.endTransmission() == 0) return true;
    delay(1);
  } while (millis() - start < 20);
  return false;
}

void command(char *line) {
  char *star = strchr(line, '*');
  if (!star || strlen(star + 1) != 4) { reply(0, "ERR", "FRAME"); return; }
  uint16_t expected = 0;
  for (uint8_t i = 1; i <= 4; i++) {
    int v = nibble(star[i]);
    if (v < 0) { reply(0, "ERR", "CRC"); return; }
    expected = (expected << 4) | v;
  }
  *star = 0;
  if (crc16(line) != expected) { reply(0, "ERR", "CRC"); return; }
  char *tokens[7];
  uint8_t count = 0;
  char *state;
  for (char *p = strtok_r(line, " ", &state); p; p = strtok_r(NULL, " ", &state)) {
    if (count == 7) { reply(0, "ERR", "ARGS"); return; }
    tokens[count++] = p;
  }
  uint32_t id, dev, addr, n;
  if (count < 2 || !number(tokens[0], 65535, id)) { reply(0, "ERR", "ARGS"); return; }
  if (!strcmp(tokens[1], "HELLO") && count == 2) {
    reply(id, "OK", "EEPROM_UNO_V1"); return;
  }
  if (count < 3 || !number(tokens[2], 87, dev) || dev < 80) {
    reply(id, "ERR", "DEVICE"); return;
  }
  if (!strcmp(tokens[1], "PROBE") && count == 3) {
    Wire.beginTransmission((uint8_t)dev);
    reply(id, Wire.endTransmission() == 0 ? "OK" : "ERR", "PROBE"); return;
  }
  bool writing = !strcmp(tokens[1], "WRITE");
  if ((!writing && strcmp(tokens[1], "READ")) || count != (writing ? 6 : 5) ||
      !number(tokens[3], 32767, addr) || !number(tokens[4], BLOCK, n) ||
      n == 0 || addr + n > 32768 || (writing && addr % 64 + n > 64)) {
    reply(id, "ERR", "RANGE"); return;
  }
  uint8_t data[BLOCK], verify[BLOCK];
  if (writing) {
    if (strlen(tokens[5]) != n * 2) { reply(id, "ERR", "HEX"); return; }
    for (uint8_t i = 0; i < n; i++) {
      int a = nibble(tokens[5][i*2]), b = nibble(tokens[5][i*2+1]);
      if (a < 0 || b < 0) { reply(id, "ERR", "HEX"); return; }
      data[i] = a * 16 + b;
    }
    if (!writeMemory(dev, addr, n, data)) { reply(id, "ERR", "I2C_WRITE"); return; }
    if (!readMemory(dev, addr, n, verify)) { reply(id, "ERR", "I2C_READ"); return; }
    if (memcmp(data, verify, n)) { reply(id, "ERR", "VERIFY"); return; }
    reply(id, "OK", "WRITTEN");
  } else {
    if (!readMemory(dev, addr, n, data)) { reply(id, "ERR", "I2C_READ"); return; }
    char hex[BLOCK*2+1];
    const char digits[] = "0123456789ABCDEF";
    for (uint8_t i = 0; i < n; i++) {
      hex[i*2] = digits[data[i] >> 4]; hex[i*2+1] = digits[data[i] & 15];
    }
    hex[n*2] = 0;
    reply(id, "OK", hex);
  }
}

void setup() {
  digitalWrite(WP_PIN, HIGH);
  pinMode(WP_PIN, OUTPUT);
  Serial.begin(115200);
  Wire.begin();
  Wire.setClock(100000);
  Wire.setWireTimeout(25000, true);
}

void loop() {
  if ((used || discard) && millis() - lastByte > 1000) {
    used = 0; discard = false;
  }
  while (Serial.available()) {
    char c = Serial.read(); lastByte = millis();
    if (c == '\n') {
      if (discard) reply(0, "ERR", "OVERFLOW");
      else if (used) { input[used] = 0; command(input); }
      used = 0; discard = false;
    } else if (c != '\r' && !discard) {
      if (used < sizeof(input)-1) input[used++] = c;
      else discard = true;
    }
  }
}

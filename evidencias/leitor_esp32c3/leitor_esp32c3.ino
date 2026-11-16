// AT24C256C reader for ESP32-C3. Upload to the ESP32 only.
// Serial commands: INFO and DUMP, terminated by newline.
// EEPROM must be disconnected from the printer and use 3.3 V logic.
// The only I2C transmission contains two address bytes, never array data.

#include <Arduino.h>
#include <Wire.h>
#include <cstring>

constexpr int SDA_GPIO = 4;
constexpr int SCL_GPIO = 5;
constexpr uint32_t I2C_HZ = 100000;
constexpr uint8_t EEPROM_ADDRESS = 0x50;  // A2/A1/A0 low, 7-bit address.
constexpr uint32_t EEPROM_SIZE = 32768;
constexpr size_t READ_SIZE = 16;
constexpr uint16_t I2C_TIMEOUT_MS = 100;
static_assert(EEPROM_SIZE == 32768, "This reader is for a 32 KiB EEPROM");
static_assert(READ_SIZE > 0 && EEPROM_SIZE % READ_SIZE == 0, "Read size");

bool busReady = false;
char command[16] = {};
size_t commandLength = 0;
bool commandOverflow = false;

void printInfo() {
  Serial.printf(
      "EEPROM_READER_V1 ADDRESS=0x%02X SIZE=%lu SDA=%d SCL=%d HZ=%lu\n",
      static_cast<unsigned>(EEPROM_ADDRESS),
      static_cast<unsigned long>(EEPROM_SIZE), SDA_GPIO, SCL_GPIO,
      static_cast<unsigned long>(I2C_HZ));
}

bool readChunk(uint32_t offset, uint8_t* data, size_t length) {
  if (!busReady || data == nullptr || length != READ_SIZE ||
      offset >= EEPROM_SIZE || length > EEPROM_SIZE - offset) {
    Serial.println("ERROR BUS_OR_RANGE");
    return false;
  }

  // Random-read word address. Sending these two bytes alone does not
  // program the EEPROM array; no data byte is sent to the device.
  const uint8_t wordAddress[] = {
      static_cast<uint8_t>(offset >> 8), static_cast<uint8_t>(offset & 0xFF)};
  static_assert(sizeof(wordAddress) == 2, "Only word-address bytes may be sent");
  Wire.beginTransmission(EEPROM_ADDRESS);
  if (Wire.write(wordAddress, sizeof(wordAddress)) != sizeof(wordAddress)) {
    Wire.end();
    busReady = false;
    Serial.printf("ERROR TX_BUFFER ADDRESS=%04X\n", static_cast<unsigned>(offset));
    return false;
  }
  const uint8_t status = Wire.endTransmission(false);  // Repeated START next.
  if (status != 0) {
    Serial.printf("ERROR I2C_ADDRESS ADDRESS=%04X STATUS=%u\n",
                  static_cast<unsigned>(offset), static_cast<unsigned>(status));
    return false;
  }

  // Some ESP32 core versions defer the bus transaction until requestFrom.
  // Therefore status == 0 above is not treated as proof of an ACK.
  const size_t received = Wire.requestFrom(
      EEPROM_ADDRESS, static_cast<uint8_t>(length), static_cast<uint8_t>(true));
  if (received != length || Wire.available() != static_cast<int>(length)) {
    Serial.printf("ERROR SHORT_READ ADDRESS=%04X EXPECTED=%u RECEIVED=%u\n",
                  static_cast<unsigned>(offset), static_cast<unsigned>(length),
                  static_cast<unsigned>(received));
    return false;
  }
  for (size_t index = 0; index < length; ++index) {
    const int value = Wire.read();
    if (value < 0) {
      Serial.printf("ERROR RX_BUFFER ADDRESS=%04X\n",
                    static_cast<unsigned>(offset + index));
      return false;
    }
    data[index] = static_cast<uint8_t>(value);
  }
  return true;
}

uint32_t updateCrc32(uint32_t crc, const uint8_t* data, size_t length) {
  for (size_t index = 0; index < length; ++index) {
    crc ^= data[index];
    for (uint8_t bit = 0; bit < 8; ++bit) {
      crc = (crc >> 1) ^ ((crc & 1U) ? 0xEDB88320UL : 0UL);
    }
  }
  return crc;
}

void dumpEeprom() {
  if (!busReady) {
    Serial.println("ERROR BUS_NOT_READY");
    return;
  }
  Serial.printf("BEGIN_EEPROM_V1 SIZE=%lu\n",
                static_cast<unsigned long>(EEPROM_SIZE));
  uint32_t crc = 0xFFFFFFFFUL;
  uint8_t chunk[READ_SIZE];
  constexpr char hexDigits[] = "0123456789ABCDEF";
  char line[4 + 1 + 4 + 1 + READ_SIZE * 2 + 1];

  for (uint32_t offset = 0; offset < EEPROM_SIZE; offset += READ_SIZE) {
    if (!readChunk(offset, chunk, sizeof(chunk))) return;
    crc = updateCrc32(crc, chunk, sizeof(chunk));
    snprintf(line, sizeof(line), "DATA %04X ", static_cast<unsigned>(offset));
    for (size_t index = 0; index < READ_SIZE; ++index) {
      line[10 + 2 * index] = hexDigits[chunk[index] >> 4];
      line[11 + 2 * index] = hexDigits[chunk[index] & 0x0F];
    }
    line[10 + READ_SIZE * 2] = '\0';
    Serial.println(line);
    delay(0);  // Yield to the USB/serial and watchdog tasks.
  }
  Serial.printf("END_EEPROM_V1 SIZE=%lu CRC32=%08lX\n",
                static_cast<unsigned long>(EEPROM_SIZE),
                static_cast<unsigned long>(crc ^ 0xFFFFFFFFUL));
  Serial.flush();
}

void setup() {
  Serial.begin(115200);
  busReady = Wire.begin(SDA_GPIO, SCL_GPIO, I2C_HZ);
  Wire.setTimeOut(I2C_TIMEOUT_MS);
  printInfo();
  if (!busReady) Serial.println("ERROR I2C_INIT");
}

void loop() {
  while (Serial.available()) {
    const int incoming = Serial.read();
    if (incoming < 0) break;
    const char c = static_cast<char>(incoming);
    if (c == '\r') continue;
    if (c == '\n') {
      if (commandOverflow) {
        Serial.println("ERROR COMMAND_TOO_LONG");
      } else if (commandLength > 0) {
        command[commandLength] = '\0';
        if (std::strcmp(command, "INFO") == 0) printInfo();
        else if (std::strcmp(command, "DUMP") == 0) dumpEeprom();
        else Serial.println("ERROR UNKNOWN_COMMAND");
      }
      commandLength = 0;
      commandOverflow = false;
    } else if (!commandOverflow) {
      if (commandLength + 1 >= sizeof(command) || c < 0x20 || c > 0x7E) {
        commandOverflow = true;
      } else {
        command[commandLength++] = c;
      }
    }
  }
  delay(1);
}

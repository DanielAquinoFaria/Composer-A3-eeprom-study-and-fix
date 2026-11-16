# Firmware compilado para Arduino Uno

`eeprom_uno.hex` foi compilado nesta entrega a partir de `../eeprom_uno/eeprom_uno.ino` usando Arduino AVR Boards 1.8.6 e avr-gcc 7.3.0-atmel3.6.1-arduino7.

- Destino: Uno R3 / ATmega328P / 16 MHz.
- Programa: 8.466 bytes; RAM estática: 721 bytes.
- Formato Intel HEX, **sem bootloader**.
- SHA-256: `e61d928a9e7432a3c4a4fbf56c2bad197fab0b5a767a5ab2f22f0f13c14dcde0`.

O caminho recomendado é abrir o sketch no Arduino IDE, selecionar Arduino Uno e carregar pela USB. O HEX é fornecido para arquivamento e usuários que já utilizam uma ferramenta de upload configurada para o bootloader do Uno. Não é uma imagem completa para substituir bootloader/fuses via ISP.

Não gravar esse arquivo na AT24C256C, na Ultratronics, no Mega ou no Uno R4. A [imagem da EEPROM](../../imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin) fica em `gravador/imagens/` a partir da raiz do pacote.

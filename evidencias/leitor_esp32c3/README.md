> Recurso histórico de aquisição. A solução final confirmada usa Arduino Uno; veja o [relatório](../../RELATORIO.md). Os limites e testes abaixo descrevem a etapa original do leitor ESP32-C3.

# Cópia da EEPROM com ESP32-C3 Mini

Este procedimento usa o ESP32 como leitor da AT24C256C fora da impressora. O sketch destina-se ao ESP32-C3; não deve ser enviado à Ultratronics nem ao Composer Flasher.

O sketch só inicia uma aquisição ao receber `DUMP`. Cada transação I²C envia os dois bytes do endereço dentro da EEPROM e depois recebe 16 bytes. Não há comando de programação de dados, apagamento ou teste de padrões. O endereço I²C é `0x50`, SDA é GPIO4, SCL é GPIO5 e a frequência é 100 kHz.

## 1. Preparar o ESP32 sem a EEPROM conectada

1. Abrir `leitor_esp32c3.ino` no Arduino IDE.
2. Selecionar a placa `ESP32C3 Dev Module`, no pacote `esp32` da Espressif.
3. Para placas Mini com USB ligado ao próprio C3, selecionar `USB CDC On Boot: Enabled`. Para placa com conversor USB–UART, verificar o circuito antes de escolher a porta serial. A revisão Mini não foi identificada por foto/esquema nesta análise.
4. Selecionar a porta do **ESP32**, não a porta da impressora. Enviar o sketch somente ao ESP32.
5. Abrir o monitor serial em 115200, selecionar fim de linha Newline ou CR+LF e enviar `INFO`.

Resposta esperada:

```text
EEPROM_READER_V1 ADDRESS=0x50 SIZE=32768 SDA=4 SCL=5 HZ=100000
```

`INFO` não faz acesso à EEPROM. A mensagem espontânea do boot pode não aparecer se o monitor abrir depois; enviar `INFO` obtém a identificação de novo. Fechar o monitor e retirar o USB antes de ligar os fios.

## 2. Isolar a placa da EEPROM e conferir o circuito

1. Desligar a impressora, retirar sua alimentação e retirar o USB da impressora.
2. Desconectar o módulo da EEPROM da Ultratronics e de outros circuitos. Não deixar alimentação, SDA ou SCL ligados à controladora. Durante o dump, o ESP32 será o único controlador do barramento.
3. Identificar o pino 1 do chip pela marca do encapsulamento e conferir a pinagem do datasheet. A posição do texto impresso não basta para identificar o pino 1.
4. Conferir por continuidade quais contatos do conector levam aos pinos do chip. A pinagem do conector do módulo ainda não foi determinada. Não usar a posição física do contato como se fosse o número do pino do chip.
5. Conferir como VCC, A0/A1/A2, WP e os resistores de SDA/SCL estão ligados. Se o módulo tiver regulador ou outros circuitos, determinar o caminho de alimentação antes de aplicar tensão. Alimentar a EEPROM a 3,3 V exige que o circuito conectado a ela também aceite essa alimentação.

## 3. Conexão

Fazer as ligações com o ESP32 sem USB e o módulo sem alimentação. Esta tabela identifica **pinos do chip SOIC/TSSOP**, não os contatos do módulo:

| ESP32-C3 | AT24C256C | Função |
|---|---|---|
| `3V3` | Pino 8, VCC | Alimentação do circuito conferido para 3,3 V |
| `GND` | Pino 4, GND | Referência |
| `GPIO4` / `IO4` | Pino 5, SDA | Dados I²C |
| `GPIO5` / `IO5` | Pino 6, SCL | Clock I²C |

`GPIO4` e `GPIO5` significam os GPIOs do C3; não significam quarto e quinto terminais da placa. Confirmar os rótulos da revisão Mini em uso. Os GPIOs podem ser alterados no sketch, mas o coletor também verifica esses números na identificação; manter ambos coerentes se houver mudança.

Se o módulo não tiver pull-ups, usar um resistor de 4,7 kΩ de SDA para 3V3 e outro de SCL para 3V3. Considerar os resistores já presentes; não acrescentar resistores em paralelo sem verificar o circuito. Não ligar pull-ups a 5 V. Usar fios curtos.

Os pinos A0/A1/A2 determinam o endereço. O fonte da Composer procura `0x50`, que corresponde aos três em nível zero. Preservar as conexões da placa e conferir o estado; não aterrar pinos sem conhecer o circuito. Se o endereço da placa for outro, interromper e registrar a diferença antes de adaptar o leitor.

WP, pino 7, em VCC bloqueia gravação e permite leitura. Só é possível usar essa proteção após conferir a ligação existente. **Não ligar WP a 3V3 se o módulo já o conecta diretamente a GND.** O procedimento não exige alterar WP: o software do leitor não envia dados para programação do array.

Conectar apenas o USB do ESP32. Conferir com multímetro VCC no chip e os níveis de SDA/SCL em repouso. O objetivo é aproximadamente 3,3 V nessas linhas, sem fonte da impressora nem pull-up para 5 V. Se houver tensão ou ligação diferente do circuito previsto, retirar o USB e conferir antes da aquisição.

## 4. Coletar três dumps

O computador desta sessão tem Python e pyserial instalados. Não foi aberta nenhuma porta para testar conexão ao ESP32.

Fechar o monitor serial do Arduino. No PowerShell, entrar nesta pasta:

```powershell
# Partindo da raiz do pacote consolidado:
Set-Location -LiteralPath 'evidencias/leitor_esp32c3'
```

Executar, trocando `COM7` pela porta do ESP32:

```powershell
python .\coletar_eeprom.py --port COM7 --label A
```

O programa identifica o leitor antes de enviar `DUMP`, realiza três aquisições e salva uma pasta de sessão em `dumps`. Não envia comandos G-code. A abertura da COM pode reiniciar ou reenunciar o ESP32; o coletor espera a identificação, sem prometer impedir o reset.

Cada sessão contém arquivos como:

```text
handshake.raw.log
reading_001.raw.log
reading_001.bin
reading_002.raw.log
reading_002.bin
reading_003.raw.log
reading_003.bin
manifest.json
```

Antes de salvar cada `.bin`, o coletor exige 2048 linhas de 16 bytes em sequência, total de 32768 bytes e CRC32 correspondente ao enviado pelo leitor. O CRC32 detecta alteração na transferência ESP32–computador; não valida o CRC MKA12/SC12 nem os parâmetros da máquina.

O manifesto inclui identificação A/B, data em UTC, método, configuração, SHA-256 de cada arquivo e comparação entre leituras. Ele não mede a tensão nem confirma qual placa foi conectada. Registrar em `notas.txt` dentro da sessão: marcação do chip, placa A/B, modelo/revisão do ESP32, versão do core, tensão medida, identificação dos fios e qualquer intervenção.

O programa retorna código 0 quando a coleta termina sem divergência, 1 em falha e 2 quando os dumps passam na verificação do transporte, mas diferem entre si. Nesse último caso, o manifesto registra `comparison_mismatch`; guardar os arquivos e investigar antes de escrever na EEPROM.

Para a placa B: retirar o USB do ESP32, trocar o módulo sem alimentação, conferir as ligações e repetir:

```powershell
python .\coletar_eeprom.py --port COM7 --label B
```

Não trocar módulos com alimentação. As pastas de sessão são distintas e o programa não substitui arquivos já existentes.

## 5. Resultado e falhas

- Cada `.bin` aceito deve ter exatamente 32768 bytes. As três aquisições da mesma placa devem produzir o mesmo SHA-256. Igualdade demonstra repetibilidade das aquisições; não demonstra que os valores da EEPROM estão de acordo com a máquina.
- Divergência entre leituras exige investigação de contato, alimentação, forma de onda e aquisição antes de atribuir defeito de retenção ao chip. Guardar todas as cópias.
- `ERROR SHORT_READ ...`: a biblioteca não entregou os 16 bytes solicitados. O leitor não preenche a falha com `0xFF`. Conferir alimentação, GND, SDA/SCL, pull-ups, isolamento e endereço. WP não impede leitura.
- `ERROR I2C_ADDRESS ...`: o driver rejeitou a etapa do endereço. Alguns cores só realizam essa transação junto com a leitura; por isso o tamanho recebido também é conferido.
- Sem `INFO`: conferir sketch, porta, placa selecionada, USB CDC e outro programa ocupando a COM. A identificação deve corresponder ao leitor antes de tentar ler a EEPROM.
- Em erro, o coletor guarda o log e os bytes recebidos com extensão `.partial`, sem apresentar o arquivo como dump válido. Não renomear `.partial` para `.bin`.

Não enviar M500/M501/M502, não abrir o Composer Flasher e não editar menus da impressora durante esta coleta. A impressora fica fora do circuito do leitor.

## 6. Alternativa sem captura serial automática

No monitor serial do Arduino, 115200 e Newline, enviar `DUMP`. Copiar a saída completa, de `BEGIN_EEPROM_V1` até `END_EEPROM_V1`, para um arquivo de texto sem editar linhas nem acrescentar timestamps. A área de saída deve comportar 2048 linhas de dados por aquisição; se o monitor descartar linhas, o conversor rejeitará a captura.

Converter o arquivo, sem precisar de pyserial:

```powershell
python .\coletar_eeprom.py --from-log .\captura_A.txt --label A
```

Esse modo aceita uma ou mais aquisições completas no mesmo arquivo e também rejeita perda de linhas ou CRC diferente. A coleta automática evita depender da capacidade do monitor para reter a saída.

## 7. Verificação feita nesta sessão

O sketch foi compilado com Arduino-ESP32 2.0.8 para `esp32:esp32:esp32c3:CDCOnBoot=cdc`. Usa 243664 bytes de programa e 16092 bytes de variáveis globais. O coletor é verificado por testes de protocolo, truncamento, erros, comparação de leituras e preservação de arquivos; os testes não abrem portas.

Os 14 testes passaram. SHA-256 das fontes verificadas:

```text
leitor_esp32c3.ino  274619c3ad9880c682f95ff739d136d313ceb3013edf35c374d39c38d37829a4
coletar_eeprom.py  4632769672814f6b923da479c4c781e15abd88ed9d7f6666d099836c481e7d2a
```

Nenhum upload foi feito. Não houve teste do ESP32, dos níveis de tensão, do módulo, do barramento ou de uma leitura de EEPROM. A compilação e os testes no computador não substituem essas verificações.

## Referências

- [Microchip AT24C256C, capacidade, pinagem, WP e leitura por endereço](https://ww1.microchip.com/downloads/aemDocuments/documents/MPD/ProductDocuments/DataSheets/AT24C256C-I%C2%B2C-Compatible-%28Two-Wire%29-Serial-EEPROM-256-Kbit-%2832%2C768x8%29-Data-Sheet-DS20006042.pdf).
- [Espressif, I²C no Arduino](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2c.html).
- [Espressif, GPIO do ESP32-C3](https://docs.espressif.com/projects/esp-idf/en/stable/esp32c3/api-reference/peripherals/gpio.html).
- [Espressif, USB CDC On Boot](https://docs.espressif.com/projects/arduino-esp32/en/latest/guides/tools_menu.html#usb-cdc-on-boot).

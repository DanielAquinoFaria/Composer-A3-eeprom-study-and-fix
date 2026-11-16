# Montagem do gravador AT24C256C

Abra [o esquemático vetorial](esquematico_arduinos_at24c256c.svg) ou [a imagem PNG](esquematico_arduinos_at24c256c.png). Para imprimir, abra [a página de impressão](esquematico.html) no navegador.

## Placas e escopo

Use apenas **uma** placa por vez. O esquema atende Uno R3/ATmega328P, Nano clássico/ATmega328P de 5 V e Mega 2560/ATmega2560 de 5 V. Não estenda estas ligações automaticamente a Due, Nano 33, ESP32 ou outras placas de 3,3 V. O Uno R4 também usa outro core e não foi validado neste projeto.

O firmware existente foi compilado para Uno R3. As ligações alternativas Nano/Mega seguem a documentação Arduino; o upload exige selecionar a placa correta no IDE e recompilar. Não envie o HEX compilado para Uno ao Mega. No Nano clássico, selecione também a opção de processador/bootloader correspondente à sua placa. As três placas usam D7 para WP; SDA/SCL são escolhidos pela biblioteca Wire conforme a placa.

## Lista de componentes

| Referência | Quantidade | Componente / função |
|---|---:|---|
| U1 | 1 | AT24C256C, com adaptador SOIC/TSSOP se necessário |
| R1, R2 | 2 | Resistor 4,7 kΩ, 1/4 W; pull-ups de SDA e SCL |
| R3 | 1 | Resistor 10 kΩ, 1/4 W; pull-up de WP |
| C1 | 1 | Capacitor cerâmico 100 nF (marcação 104), tensão nominal de pelo menos 10 V; desacoplamento |
| — | 1 | Arduino e cabo USB de dados adequado |
| — | — | Protoboard/adaptador e fios curtos |

Resistores não têm polaridade. O capacitor cerâmico indicado também não tem polaridade. Confira se um módulo pronto já contém pull-ups: resistores adicionais em paralelo alteram a resistência equivalente.

## Identificação física do CI

O desenho abaixo é a **vista superior de SOIC/TSSOP de 8 pinos**, com a marca/entalhe para cima. A numeração segue em sentido anti-horário. O símbolo grande do esquemático é funcional: a posição gráfica dos sinais nele não reproduz a disposição física do encapsulamento.

```text
                  marca / entalhe
                    +---U---+
              A0  1 |       | 8  VCC
              A1  2 |       | 7  WP
              A2  3 |       | 6  SCL
             GND  4 |       | 5  SDA
                    +-------+
```

Confirme a marca do pino 1 no componente. Para UDFN/VFBGA use a figura correspondente do datasheet; VFBGA pode ser apresentado em vista inferior. Este datasheet não especifica uma versão DIP desse CI.

## Ligações, fio por fio

| EEPROM | Uno R3 | Nano clássico | Mega 2560 | Ligação adicional |
|---|---|---|---|---|
| 1 — A0 | GND | GND | GND | Define bit 0 do endereço como zero |
| 2 — A1 | GND | GND | GND | Define bit 1 do endereço como zero |
| 3 — A2 | GND | GND | GND | Define bit 2 do endereço como zero |
| 4 — GND | GND | GND | GND | Um terminal de C1 |
| 5 — SDA | A4/SDA | A4 | D20/SDA | R1 de 4,7 kΩ entre SDA e 5 V |
| 6 — SCL | A5/SCL | A5 | D21/SCL | R2 de 4,7 kΩ entre SCL e 5 V |
| 7 — WP | D7 | D7 | D7 | R3 de 10 kΩ entre WP e 5 V |
| 8 — VCC | 5V | 5V | 5V | Outro terminal de C1 |

Os símbolos +5 V do esquemático são uma única rede elétrica; todos os GND também. Use o pino **5V**, não VIN. A alimentação vem do Arduino conectado à USB. O GND precisa ser comum.

A0/A1/A2 na tabela são entradas da EEPROM, **não os pinos analógicos do Arduino**. Com esses três pinos no GND, o endereço I²C é **0x50**. A4/A5 do Uno são compartilhados com seus conectores SDA/SCL dedicados; não são dois barramentos diferentes.

## Os resistores são ramificações

Não coloque R1/R2/R3 em série entre Arduino e EEPROM. A ligação do sinal é direta; o resistor liga essa mesma linha à alimentação:

```text
Arduino SDA --------+-------- EEPROM SDA
                    |
                  [4,7k] R1
                    |
                   +5 V

Arduino SCL --------+-------- EEPROM SCL
                    |
                  [4,7k] R2
                    |
                   +5 V

Arduino D7 ---------+-------- EEPROM WP
                    |
                   [10k] R3
                    |
                   +5 V
```

SDA/SCL precisam de pull-ups para comunicação I²C. R3 mantém WP alto durante reset, enquanto D7 ainda não está dirigindo a saída. No firmware, D7 fica alto em repouso e baixo durante o envio de cada escrita. WP alto bloqueia escrita; baixo permite. A leitura é permitida em ambos os estados.

**Não ligue WP diretamente a 5 V com D7 conectado.** Quando D7 tentar baixar, isso criaria conflito elétrico. A conexão de WP à alimentação deve passar por R3. Um capacitor entre WP e 5 V não substitui esse resistor: ele pode transmitir transientes, mas não sustenta a proteção em corrente contínua.

Para somente leitura com bloqueio permanente de escrita: desligue a alimentação, desconecte D7 do WP e então ligue WP diretamente ao VCC. Essa é uma alternativa de montagem, não deve ser somada ao circuito de D7.

## Capacitor de alimentação

C1 fica **entre os pinos 8 (VCC) e 4 (GND)**, o mais próximo possível da EEPROM. Não fica em série com a alimentação nem conectado ao WP. Sua função é reduzir ruídos locais de alimentação.

## Sequência de uso

1. Desconecte o USB e monte o circuito, conferindo orientação, alimentação e conexões.
2. Confirme que a EEPROM está isolada da eletrônica da impressora. Não conecte o 5 V do Uno ao barramento original de 3,3 V e não alimente o conjunto por duas fontes.
3. Conecte o USB. No IDE, selecione a placa/porta corretas e carregue `firmware/eeprom_uno/eeprom_uno.ino`, com Arduino AVR Boards compatível com `Wire.setWireTimeout`.
4. Feche o Monitor Serial. Abra a interface do projeto, selecione a COM e endereço **0x50**, sem modo Simulação.
5. Faça uma leitura completa de 32.768 bytes e salve o backup. Uma segunda leitura igual ajuda a conferir repetibilidade.
6. Para gravar uma imagem completa, use endereço inicial **0x0000**. Aguarde a verificação e faça uma releitura se precisar comparar o arquivo integral.

No Monitor Serial, um teste de comunicação com o Arduino é `1 HELLO*7DF0`, a 115200 baud e com Nova linha. A resposta esperada é `1 OK EEPROM_UNO_V1*48C9`. Esse teste confirma o protocolo do Arduino; não comprova a presença da EEPROM. A interface também executa PROBE ao conectar.

## Pontos para conferir com multímetro

| Medição | Condição esperada neste circuito |
|---|---|
| Pino 8 em relação ao pino 4 | Alimentação nominal de 5 V |
| WP em repouso | Próximo de VCC |
| SDA/SCL ociosos | Próximos de VCC, quando o barramento não está ocupado |
| A0/A1/A2 | Próximos de GND |

Pulsos em WP e comunicação SDA/SCL são rápidos; um multímetro pode mostrar apenas valores médios. Use osciloscópio/analisador lógico para observar as transações. Faça continuidade/resistência com o circuito desligado.

## Fontes e validação

- Datasheet local: [AT24C256C](../../referencias/datasheets/atmel-8568-seeprom-at24c256c-datasheet.pdf), pinagem e descrição de WP.
- [Arduino: tabela de pinos Wire/I²C](https://github.com/arduino/docs-content/blob/main/content/learn/05.communication/01.wire/wire.md).
- [Arduino: referência Wire](https://github.com/arduino/reference-en/blob/master/Language/Functions/Communication/Wire.adoc).
- Firmware do projeto: `WP_PIN = 7`, `Wire.begin()`, I²C a 100 kHz e serial a 115200 baud.

O desenho foi conferido visualmente. Não foi realizada validação elétrica em bancada. Nano e Mega têm aqui mapeamento de ligações; compilação/upload e operação física nessas placas ainda não foram verificados.

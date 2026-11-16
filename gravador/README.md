> Esta é a documentação do gravador incluído no [pacote de recuperação](../README.md). Em 16/11/2026, o operador confirmou a resolução com Uno e a imagem indicada no [relatório final](../RELATORIO.md). Execute os comandos desta página dentro da pasta `gravador/`.

# Leitor e gravador AT24C256C com Arduino Uno

Projeto dividido em duas frentes:

- **Firmware** C++ para Arduino Uno R3/ATmega328P: controla a EEPROM por I²C e recebe comandos pela USB serial.
- **Interface desktop** Python/Tkinter: seleciona a porta COM, endereço I²C e modo de leitura, gravação ou verificação.

## Começar

1. Monte as ligações abaixo com a alimentação desligada.
2. Abra `firmware/eeprom_uno/eeprom_uno.ino` no Arduino IDE. Instale/selecione **Arduino AVR Boards 1.8.6 ou compatível com Wire.setWireTimeout**, placa **Arduino Uno** e a porta correspondente. Carregue o sketch. Feche o Monitor Serial antes de usar a interface.
3. Instale Python 3.10 ou superior com Tcl/Tk. No terminal, nesta pasta:

   ```powershell
   python -m pip install -r requirements.txt
   python desktop/app.py
   ```

   No Windows, após instalar as dependências, também pode abrir `iniciar.bat`.
4. Selecione a porta, deixe o endereço em `0x50` para A0/A1/A2 aterrados e clique **Conectar**.
5. Selecione **Leitura**, endereço `0x0000`, quantidade `32768` e um arquivo de destino. Execute para salvar o backup completo antes da primeira gravação.
6. Para gravar, selecione **Gravação**, o arquivo `.bin` e o endereço inicial. A aplicação usa o tamanho do arquivo, pede confirmação e verifica os dados gravados. **Verificação** compara um arquivo com a EEPROM sem alterá-la.

Para experimentar sem Arduino, marque **Simulação (sem hardware)** antes de conectar. A memória começa preenchida com `FF` e existe apenas enquanto essa conexão simulada estiver aberta. Nenhuma porta serial é aberta nesse modo; os arquivos de leitura continuam sendo salvos normalmente.

## Componentes e ligações

- Arduino Uno R3 (5 V / ATmega328P) e cabo USB de dados.
- AT24C256C, adaptador de encapsulamento quando necessário e protoboard.
- Dois resistores de 4,7 kΩ para SDA/SCL, um de 10 kΩ para WP e um capacitor cerâmico de 100 nF.
- Fios curtos; configuração inicial I²C a 100 kHz.

Pinagem abaixo para **SOIC/TSSOP de 8 pinos, vista superior**. O componente não é fornecido como DIP neste datasheet: use adaptador adequado. Confira a marca do pino 1. Para UDFN/VFBGA, consulte a figura específica do datasheet; VFBGA é mostrado em vista inferior.

| Pino EEPROM | Sinal | Ligação |
|---|---|---|
| 1 | A0 | GND |
| 2 | A1 | GND |
| 3 | A2 | GND |
| 4 | GND | GND do Uno |
| 5 | SDA | A4/SDA do Uno e resistor de 4,7 kΩ para 5 V |
| 6 | SCL | A5/SCL do Uno e resistor de 4,7 kΩ para 5 V |
| 7 | WP | D7 do Uno e resistor de 10 kΩ para 5 V |
| 8 | VCC | 5 V do Uno |

Coloque o capacitor de 100 nF entre VCC e GND, próximo à EEPROM. SDA/SCL dedicados no Uno R3 são os mesmos sinais de A4/A5.

```text
Arduino Uno                        AT24C256C (vista superior)
                                  +-----U-----+
GND ------------------------------|1 A0  VCC 8|---- 5V
GND ------------------------------|2 A1   WP 7|---- D7
GND ------------------------------|3 A2  SCL 6|---- A5/SCL
GND ------------------------------|4 GND SDA 5|---- A4/SDA
                                  +-----------+
5V ---[4,7k]--- SDA       5V ---[4,7k]--- SCL
5V ---[10k]---- WP        5V ---|| 100nF--- GND
```

WP alto protege toda a memória; WP baixo permite gravar. O resistor de 10 kΩ mantém a proteção durante reset/boot do Uno. O firmware mantém D7 alto e só o baixa durante cada comando físico de gravação. Não conecte WP diretamente a 5 V ao usar D7: use o resistor. Para leitura permanentemente protegida, pode ligar WP a 5 V **com D7 desconectado**; gravações serão bloqueadas.

Endereço I²C de 7 bits: `0x50 | (A2 << 2) | (A1 << 1) | A0`. Ligue cada entrada a GND (0) ou VCC (1) e selecione o valor correspondente entre `0x50` e `0x57`. A interface usa endereços de 7 bits, não `0xA0/0xA1`.

**Uso em placa existente:** este esquema é para a EEPROM isolada, alimentada a 5 V pelo Uno. Não conecte diretamente o Uno de 5 V a um barramento de 3,3 V, nem alimente simultaneamente a placa original e o circuito de bancada. Prefira remover/isolar a EEPROM. Programação no circuito exige analisar alimentação, níveis, pull-ups e os outros mestres do barramento; pode exigir conversor de nível. O fato de a EEPROM aceitar 5 V não significa que o restante da placa aceite.

## Comportamento

- Capacidade de 32.768 bytes (256 **kbits**), endereços `0x0000` a `0x7FFF`.
- Endereço inicial decimal ou hexadecimal com prefixo `0x`. Quantidade de leitura em decimal.
- Arquivos binários puros, sem cabeçalho: o byte zero do arquivo corresponde ao endereço inicial selecionado. Intel HEX, textos hexadecimais e arquivos de firmware de outros formatos não são convertidos.
- Gravações parciais preservam os bytes fora da faixa. Arquivo vazio ou que ultrapasse o final da memória é rejeitado, sem truncamento ou preenchimento automático.
- O dispositivo não exige apagamento prévio: cada gravação substitui os bytes selecionados.
- Buffer Wire de 32 bytes: cada bloco contém no máximo 30 bytes de dados mais dois bytes de endereço. Nenhum bloco cruza uma página de 64 bytes.
- Após cada gravação, ACK polling aguarda a conclusão do ciclo interno (datasheet: até 5 ms; limite de espera do firmware: 20 ms). Cada bloco é relido e comparado; ao final, o PC faz outra verificação integral.
- Leitura usa endereço de memória em dois bytes, repeated START e leitura sequencial.
- CRC-16/CCITT-FALSE e sequência protegem os comandos e respostas seriais. Não há repetição automática de gravação após falha, pois o resultado do último bloco pode ser desconhecido.
- As operações rodam em segundo plano; a interface continua respondendo. Cancelar interrompe entre blocos. Uma gravação cancelada/falha pode deixar parte da memória alterada; não existe rollback. Se cancelar na verificação final, os bytes já foram gravados, mas a conferência integral não terminou.
- A leitura só substitui o arquivo de destino após receber toda a faixa. Exibe prévia hexadecimal/ASCII de até 256 bytes e SHA-256 do conteúdo.
- Um ACK no endereço I²C não identifica o modelo do chip. Confirme fisicamente que se trata de AT24C256C antes de gravar.
- Conexão/porta/endereço são capturados ao clicar Conectar. Desconecte para mudar o dispositivo.

## Estrutura

```text
firmware/eeprom_uno/eeprom_uno.ino  Firmware Arduino
 desktop/app.py                    Interface Tkinter
 desktop/eeprom.py                 Protocolo e operações de memória
 tests/test_eeprom.py              Testes de comunicação e memória
 tests/test_gui.py                 Teste de fluxo da interface simulada
 tools/build_firmware.py           Compilação local com AVR já instalado
 iniciar.bat                      Inicializador Windows
 requirements.txt                 Dependência pyserial
 PROTOCOLO.md                     Especificação serial
 VALIDACAO.md                     Evidências e limitações dos testes
```

## Testar e compilar

```powershell
python -m unittest discover -s tests -v
python tools/build_firmware.py
```

O teste da interface exige uma sessão gráfica com Tk disponível. O compilador auxiliar usa o core AVR e o avr-gcc existentes em `%LOCALAPPDATA%/Arduino15/packages/arduino`; aceita outro caminho com `--arduino-packages`. Não instala ferramentas nem faz upload. O Arduino IDE é o caminho principal para compilar/carregar. Saída auxiliar: `build/eeprom_uno.hex` (sem bootloader).

## Diagnóstico

| Sintoma | Ação |
|---|---|
| Nenhuma porta | Confira cabo USB de dados e driver da placa; clique Atualizar |
| Porta ocupada | Feche Monitor Serial e outros programas que usam a mesma COM |
| Arduino não responde | Confira Uno/firmware/porta; aguarde o reset ao conectar |
| PROBE ou I2C_READ/I2C_WRITE | Confira A0–A2, GND comum, alimentação, SDA/SCL e pull-ups |
| VERIFY/divergência | Confira WP/D7, contato elétrico e alimentação; releia antes de tentar novamente |
| CRC ou sequência | Reconecte e confira USB; a sessão é encerrada para evitar dados fora de sincronia |
| Falha/cancelamento durante escrita | Releia e compare a faixa; restaure o backup se necessário |

## Referências

- Datasheet: consulte [referência e condições de distribuição](datasheets/README.md), revisão Atmel-8568F, janeiro/2015. Pinagem: p. 2; WP: p. 3; organização: p. 4; endereçamento: p. 9; gravação/polling: p. 10; leituras: pp. 11–12.
- [Arduino Wire: buffer de comunicação](https://github.com/arduino/reference-en/blob/master/Language/Functions/Communication/Wire.adoc).
- [Arduino Wire.setWireTimeout](https://docs.arduino.cc/language-reference/en/functions/communication/wire/setWireTimeout/).
- [API oficial pySerial](https://pyserial.readthedocs.io/en/stable/pyserial_api.html).

## Esquemático detalhado

Veja o [guia de montagem](hardware/MONTAGEM.md), o [esquemático SVG](hardware/esquematico_arduinos_at24c256c.svg) ou a [página para impressão](hardware/esquematico.html). Inclui Uno R3, Nano clássico e Mega 2560 de 5 V, com diferenças de pinagem e limites de validação.


## Reprodução e dependências

Veja [REPRODUZIR.md](REPRODUZIR.md) para os caminhos, toolchains e comandos de geração, e [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) para proveniência, licenças e exclusões.

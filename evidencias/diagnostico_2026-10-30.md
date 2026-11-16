> Diagnóstico de 30/10/2026, preservado como etapa da investigação. A comparação posterior localizou o valor Y no dump; a resolução foi confirmada pelo operador. Consulte o [relatório final](../RELATORIO.md). Links locais adaptados à pasta consolidada.

# Composer A3 — diagnóstico e sequência de testes

Data: 30/10/2026.

Base: leitura do [dossiê](dossie_inicial.md), logs, fonte MKA, pacotes do gravador e datasheets. Nenhum comando foi enviado à impressora. Não houve gravação de firmware, configuração ou EEPROM.

## 1. Resultado e limite da conclusão

O fonte contém uma cadeia de falhas que explica os registros: a leitura altera variáveis de execução antes de verificar o CRC; a restauração após erro deixa campos sem redefinição; a interface pode gravar esses campos com outro CRC; o boot permite homing e troca de ferramenta com base apenas no sucesso da carga do bloco SYSTEM.

O campo que liga os registros ao movimento é `tools.switch_offset_y`, exibido por `M503` como `M217 ... Yovf`. Ele participa do destino Y na troca de ferramenta. Zerar `M218` não modifica esse campo.

A origem da alteração dos bytes continua sem determinação: conteúdo/layout, falha na gravação, comunicação I²C, alimentação ou retenção. A troca de uma placa de EEPROM por outra, sem comparar seus conteúdos, não separa essas causas. Também falta demonstrar a equivalência do código dessas funções com as instruções do MCU em execução. Os logs e a identidade do pacote sustentam a correlação, mas não substituem essa verificação.

## 2. Correlação entre registros e fonte

| Registro/comportamento | Mecanismo no fonte | Conclusão |
|---|---|---|
| CRC USR armazenado 64898, calculado 14619; depois `Default Settings Loaded`, mas `M217 Yovf` e `M145 H8000 B56197` persistem | `Load_Usr()` lê esses campos na RAM antes do CRC; `Factory_Settings()` não os redefine | A rejeição do registro não elimina todos os efeitos da leitura |
| Após editar o menu: `M218 T1 X0 Y0 Z0`, `MKA12` aceito com 117 bytes/CRC 24754, mas `M217 Yovf` permanece | O menu modifica `hotend_offset` e chama a gravação de todo USR | A gravação pode tornar o bloco aceito pelo CRC sem corrigir o offset da troca |
| Homing termina; movimento Y passa a um valor sem relação com o curso | A troca soma `switch_offset_y` a pontos da rota `K1` e envia o destino ao planner | Mecanismo compatível com o valor do dossiê; igualdade do valor exige bytes ou instrumentação |
| Logo permanece e apenas emergência responde | A tela de status é ativada depois de homing/troca; a espera do planner recebe comandos e trata M112 por outro caminho | Não é necessário supor travamento do LCD para explicar o sintoma |
| Outra EEPROM muda o sentido durante homing | SYSTEM guarda inversão dos motores e bits de endstop | Diferença de conteúdo pode explicar a mudança; não comprova defeito do chip |

Fontes dos registros: [log de CRC rejeitado](logs/ultimo_startInfoSoftwhor%20Anisoprint%20LLCEch.txt), [log após alteração](logs/log29-10v1.md), [captura com comandos](logs/log.txt). Os arquivos contêm registros de épocas distintas; não representam uma leitura obtida nesta análise.

## 3. Pontos do código

Os caminhos abaixo partem de `firmwares/firmware codigo fonte/MKA-firmware/`.

| Referência | Comportamento |
|---|---|
| `src/core/eeprom/eeprom.cpp:457–484` | Carrega defaults, SYSTEM e USER. Em erro USR, repete defaults e recarrega SYSTEM. Retorna apenas `sysLoaded` |
| `src/core/eeprom/eeprom.cpp:1005–1029` | Lê dados diretamente nas variáveis de execução |
| `src/core/eeprom/eeprom.cpp:1042–1068` | Confere CRC depois das atribuições |
| `src/core/eeprom/eeprom.cpp:2052–2589` | Defaults não atribuem `switch_offset_x/y`, pré-aquecimento e brilho |
| `src/core/tools/tools.cpp:52–53`; `src/lcd/nextion_hmi/NextionHMI.cpp:29–31` | Esses campos recebem valores na inicialização dos objetos, não a cada execução de defaults |
| `src/lcd/nextion_hmi/StateSettings.cpp:296–302` | Edição pelo menu grava USR inteiro |
| `src/core/commands/gcode/composer/m217.h:40–54` | `A/B` alteram o offset da troca; `X/Y` alteram pontos da rota quando existe `S` |
| `src/core/eeprom/eeprom.cpp:2968–2972` | Relatório imprime os offsets como `M217 X/Y`, sem corresponder ao parser `A/B` |
| `src/core/tools/tools.cpp:210–218` | Soma offset da troca nos pontos `K1` e chama movimento com espera |
| `src/core/mechanics/mechanics.cpp:110–112,230–258` | Transforma coordenadas, atribui destino e espera o movimento |
| `src/core/planner/planner.cpp:1914–1918` | Converte destino em passos `int32_t`; esse caminho não verifica a magnitude antes da conversão |
| `src/core/printer/printer.cpp:319–332` | Se SYSTEM carregou, executa homing e troca; só depois ativa status |
| `src/core/stepper/stepper.cpp:2364–2368`; `src/core/printer/printer.cpp:691`; `src/core/commands/commands.cpp:471` | Espera fila; recebe comandos; reconhece emergência |
| `src/core/eeprom/eeprom.cpp:554,572–573,737,758–759` | Grava/lê inversão dos motores, lógica e pull-ups dos endstops no SYSTEM |

O homing usa `home_dir` da compilação (`src/core/mechanics/mechanics.cpp:67`). A polaridade da saída DIR também depende de `stepper_dir_invert[]` carregado do SYSTEM. São mecanismos distintos.

Os offsets X −2,2 / Y −16,5 constam nos defaults do perfil A3 (`config/COMPOSER_A3_V10/Configuration_Core.h:670–672`). Sua presença depois do erro não demonstra leitura da EEPROM nem armazenamento de calibração na Flash.

## 4. Leitura/gravação I²C

O perfil A3 define `EEPROM_I2C` e `WIRE Wire1` (`Configuration_Feature.h:1120–1121`). `src/platform/I2cEeprom.cpp:75` usa endereço de dispositivo `0x50`.

1. `I2cEeprom.cpp:87–100`: grava um byte por transação; ignora o retorno de `endTransmission()` e espera 5 ms.
2. `I2cEeprom.cpp:133–145`: ignora o resultado do envio do endereço e a contagem de `requestFrom()`. Sem byte recebido, devolve `0xFF`.
3. `src/platform/HAL_DUE/HAL_eeprom_Due.cpp:85–97`: copia o retorno para RAM, acumula CRC e retorna ausência de erro. Não distingue um byte `0xFF` armazenado de uma falha de recepção.
4. `HAL_eeprom_Due.cpp:69–79`: a escrita faz releitura por byte; uma divergência retorna antes de avançar a posição.
5. `eeprom.cpp:431–432`: macros substituem `eeprom_error` em cada operação. Um sucesso depois de uma falha pode apagar o estado de erro. Se a execução continua, o deslocamento do próximo campo também pode estar incorreto.
6. `eeprom.cpp:450–452`: `Store_Settings()` declara `bool`, chama `Store_Usr()` e não retorna seu resultado.

São defeitos de tratamento no fonte. Não demonstram que ocorreram na gravação registrada.

A espera de 5 ms coincide com o máximo de escrita do AT24C256C. Sua presença, isoladamente, não demonstra violação de tempo. A recomendação é verificar ACK com prazo e propagar falhas, conforme a [Microchip](https://onlinedocs.microchip.com/oxy/GUID-FEEC2B39-7B05-43C4-AB92-C76A6F28FB70-en-US-2/GUID-0A478C13-C4D9-4697-BE62-320471DCB1DE.html). O caminho acima grava por byte: o simples cruzamento do endereço 64 não comprova rollover de página.

## 5. Mapa para comparar dumps

Mapa derivado do fonte SAM e da composição do perfil A3 que produz os tamanhos dos logs. Endereços absolutos, em bytes; confirmar a compilação antes de interpretar um dump de outra versão.

| Região/campo | Endereço decimal | Hexadecimal |
|---|---:|---|
| USER, 117 bytes | 10–126 | `0x000A–0x007E` |
| Versão USER, 6 bytes | 10–15 | `0x000A–0x000F` |
| CRC USER, 2 bytes | 16–17 | `0x0010–0x0011` |
| Steps E/U/V | 18–29 | `0x0012–0x001D` |
| Home XYZ | 30–41 | `0x001E–0x0029` |
| Offsets dos bicos | 42–65 | `0x002A–0x0041` |
| Offset X da troca, float | 66–69 | `0x0042–0x0045` |
| Offset Y da troca, float | 70–73 | `0x0046–0x0049` |
| Pré-aquecimento H/B, uint16 | 74–77 | `0x004A–0x004D` |
| Brilho | 78 | `0x004E` |
| PID, quatro conjuntos Kp/Ki/Kd | 79–126 | `0x004F–0x007E` |
| SYSTEM, 751 bytes | 4106–4856 | `0x100A–0x12F8` |
| SN/versão da máquina, 26 bytes | 32010–32035 | `0x7D0A–0x7D23` |

Referências: `src/platform/HAL_DUE/HAL_Due.h:160`, `eeprom.cpp:45–50,908–931,978–1029`. CRC: polinômio `0x1021`, início zero, sobre o payload; cabeçalho de versão/CRC excluído. Inteiros e floats devem ser interpretados em little-endian para este alvo. No USER, verificar bytes 18–126 contra o CRC em 16–17.

Derivação para depuração: o número `-74874577188028416` é representável como float32 com bits `0xDB850104`, bytes little-endian `04 01 85 DB`. Comparar esse padrão nos endereços 70–73 se a captura mostrar que o número está em `switch_offset_y`. Essa conversão não é uma leitura da EEPROM; o dossiê registra a coordenada, sem identificar seus bytes de origem. Somar centenas de milímetros a um float dessa magnitude pode manter o mesmo valor por falta de resolução.

## 6. Hardware e revisão de premissas

O [datasheet AT24C256C](../referencias/datasheets/atmel-8568-seeprom-at24c256c-datasheet.pdf), página 14, associa a marcação `2ECL` ao AT24C256C; a capacidade é 32.768 bytes. Isso sustenta o uso desse datasheet para o chip descrito, sujeito à conferência da peça e do encapsulamento.

No [datasheet SAM3X](../referencias/datasheets/Atmel-11057-32-bit-Cortex-M3-Microcontroller-SAM3X-SAM3A_Datasheet-ATSAM3X8E.pdf), tabela 4-3, para LQFP144:

- Pino 47: `NRSTB`.
- Pino 69: `NRST`.
- Pino 130: `PC0`, multiplexado com `ERASE`.

Portanto, a identificação do botão ligado ao pino 130 como outro reset precisa de revisão. Se esse sinal exercer a função ERASE e for acionado nas condições do datasheet, apaga Flash do MCU. Isso não corresponde a apagar a EEPROM no barramento I²C. Verificar continuidade com a placa sem alimentação e identificar a função do circuito antes de novo acionamento. Não confundir numeração de terminal do encapsulamento com numeração Arduino.

Fonte do fabricante: [SAM3X, pinagem e seções 6.4–6.6](https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/Atmel-11057-32-bit-Cortex-M3-Microcontroller-SAM3X-SAM3A_Datasheet.pdf).

## 7. Testes, em ordem

Executar intervenções com acionamento dos motores e aquecedores impedido, como exige o histórico de movimento. Desconexões devem ocorrer sem alimentação. Os testes abaixo são propostas; nenhum foi executado nesta análise.

1. **Preservar conteúdo e identidade.** Ler 32.768 bytes de cada EEPROM por programador ou firmware de diagnóstico, sem disputa de barramento com o MCU. Guardar placa, data, método e hash. Capturar o boot, `M503 S` e `M503 U`. Não gravar antes dessa coleta. `M503` mostra RAM; não substitui dump.
2. **Separar leitura de conteúdo.** Repetir três leituras de cada placa sem escrita e comparar bytes. Se houver diferenças, investigar alimentação/transporte/leitor. Se forem iguais, verificar layout, CRC e valores; um CRC que confere com Y fora do curso mostra conteúdo inadequado para uso, sem indicar sozinho a origem da alteração. Confirmar com outro método se o leitor puder repetir o mesmo erro.
3. **Verificar restauração no binário em execução.** Com movimento impedido e sessão apta a processar comandos, registrar `M503 U`, enviar `M502` e registrar `M503 U` novamente. Persistência de `M217 Yovf`/pré-aquecimento reproduz a omissão dos defaults. Esse teste altera parâmetros de SYSTEM na RAM; não gravar esse estado nem retomar movimento. Recarregar os blocos preservados e validar SYSTEM antes de continuar. Se a espera do boot impedir os comandos, usar build de diagnóstico com homing/troca no boot desabilitados; não contar com M112 como modo de manutenção.
4. **Isolar o campo da troca na RAM.** Depois de restabelecer SYSTEM e registrar o estado, enviar `M217 A0 B0` e consultar `M503 U`. O relatório deve passar a exibir `M217 X0.000 Y0.000`. Esse comando não realiza a troca. `M217 X0 Y0`, sem `S`, não altera o campo nesse parser. Manter `M218` fora dessa intervenção para separar os efeitos. Corrigir também os presets antes de salvar; no perfil A3 do fonte, os defaults são H230/B60 (`Configuration_Temperature.h:161–162`), ajustando-os à configuração da máquina. `M145` define presets, não manda aquecer.
5. **Localizar a espera do boot.** Em build de diagnóstico, registrar entrada/saída de `home()`, entrada de `tools.change()`, índice da rota, `K`, Y da rota, `switch_offset_y`, destino depois da transformação e número de passos antes da conversão. Se home retorna e um ponto K1 introduz o valor fora do curso, fica localizado o mecanismo. Impedir a emissão desse movimento. Comparar valores entre as placas; examinar também `stepper_dir_invert[Y]`, bits de endstop e M119 com acionamento de cada sensor. `M503` deste fonte não mostra direção/bits e `M569` sem eixos não os consulta.
6. **Verificar gravação e retenção.** Somente após validar todos os campos USR e preservar os dumps, salvar com `M500` sem `S`. Comparar dump e CRC após gravar, após reset e após retirar/reaplicar alimentação. `M500 S` também grava SYSTEM e não serve para isolar este teste. Bytes incorretos já após salvar apontam a escrita/transporte; mudança após o ciclo sem novas escritas exige investigar alimentação, retenção e eventual escrita no boot.
7. **Medir o barramento se houver erro.** Registrar VCC no chip, SDA/SCL, ACK/NACK do endereço `0x50`, os dois bytes do endereço de memória, contagem recebida, tempo de escrita e estado de WP. Conferir A0/A1/A2 e continuidade. O AT24C256C usa pinos 4 GND, 5 SDA, 6 SCL, 7 WP e 8 VCC no encapsulamento de oito terminais descrito no datasheet. Não mudar a tensão do módulo sem conferir os níveis aceitos pela interface do MCU. Testar placa/chip separado com padrão conhecido somente depois de preservar o conteúdo; comparar com o mesmo leitor e condições antes de atribuir defeito ao chip.

## 8. Correções a implementar e verificar

1. Ler blocos em estrutura temporária; verificar transporte, versão, CRC, finitude e faixas por campo antes de aplicar à execução. Rejeitar também valores finitos fora da faixa: a magnitude Y do dossiê não exige NaN ou infinito.
2. Redefinir todos os campos USER em defaults, incluindo offsets da troca, presets e brilho. Manter tratamento separado para SYSTEM e USER.
3. Bloquear homing/troca no boot quando os parâmetros exigidos para esses movimentos não forem aceitos. Não usar apenas `sysLoaded` como autorização.
4. Verificar destinos contra o envelope da troca e capacidade de representação em passos antes do planner. A rota inclui X negativo e Y fora da área de impressão; os limites precisam corresponder ao mecanismo, sem aplicar cegamente o retângulo de impressão.
5. Propagar falhas I²C, conferir contagens e ACK, usar prazo para espera/recuperação e interromper a transação na primeira falha. Não converter falha de recepção em dado `0xFF` sem estado de erro.
6. Acumular erros de EEPROM, manter posição/layout sob falha e retornar `Store_Usr()` em `Store_Settings()`. Validar o registro por releitura antes de publicar cabeçalho/CRC. Para tolerar corte de alimentação, usar cópia anterior e marcador/geração de commit.
7. Fazer o relatório imprimir `M217 A/B`, de modo que sua saída corresponda ao parser.

Verificação da correção: injetar falha de transporte e CRC; confirmar ausência de alteração parcial da execução e ausência de movimento. Gravar com releitura, interromper a gravação em pontos definidos e verificar a escolha de um registro íntegro. Repetir reset e ciclo de alimentação depois de uma gravação aceita. Compilar para a revisão A3 e validar a rota com acionamento impedido antes do teste com motores.

## 9. Cronologia e gatilho

Nos dois G-codes encontrados em `logs/gcodea`, a busca por M500/M501/M502/M217/M218 não encontrou ocorrências. O fonte da tela de impressão e seus eventos de conclusão não mostra gravação USER ao terminar a impressão. Há gravações em edição de parâmetros, presets e conclusão de calibrações (`StateSettings.cpp:302,319,335`; `StateTemperature.cpp:51,59`; `StateWizard.cpp:178,306,907`; `StateWizardZ.cpp:259`).

Como o dossiê registra calibrações antes da primeira impressão, essa etapa é um candidato a persistir o estado que só passa a ser carregado após desligar/ligar. A evidência não permite atribuir a alteração dos bytes ao fim da impressão. Comandos de host, arquivos não examinados e divergência entre fonte/binário permanecem fora dessa conclusão.

## 10. Gravador, perfil e identidade do pacote

O `MKA.bin` em `Composer Flasher/Composer A3/MKA_1.2.6_ComposerA3_v1.0.x_15-05-2024/` tem 236.720 bytes e SHA-256 `AFF23A70B3ADE6C049AD2BE86920A1C284BC802A2A35D914DB181105DD700F6F`. A comparação com o membro `MKA.bin` do pacote FW2 de 24/03/2022 produz o mesmo hash. As strings do binário identificam MKA_1.2.6, MKA12/SC12 e compilação Mar 24 2022 21:23:48, também presentes nos logs.

O FW2 é um contêiner ZIP com binário, perfis e recursos de tela. A data 2024 do pacote não representa, neste caso, mudança do código do MCU. Isso não identifica a Flash atualmente no equipamento: falta readback/hash do MCU.

O perfil `Composer A3-1.0.5.gc` define, entre outros, `M569 X0 Y1 Z1 E1 U1 V1` (linha 8), `M92 ... Z2560` (linha 10) e `M203 ... Z5` (linha 12). Ele configura a rota com `M217 T... S...`, mas não contém comando para zerar `M217 A/B`, nem `M218` ou `M145`. Portanto, reaplicar esse perfil não implica corrigir o conteúdo USER. Além disso, a gravação do gravador por `M500 S` alcança SYSTEM e USER, podendo persistir o estado USER que estiver na RAM.

Os logs de 27/08/2026 identificam tentativas com `A3-1.0.3nw`: uma termina esperando `Status:I`; outra registra erro ao salvar configuração. A segunda envia Z400/Z30 às 11:32:15. Os registros posteriores mostram Z2560/Z5, mas não há, nesses logs de flashing, demonstração de conclusão de uma aplicação do perfil 1.0.5. Não misturar o sucesso de gravação/verificação da Flash pelo bossac com o sucesso da gravação da configuração I²C.

O CIL de `Flasher.dll` associa a gravação de configuração a `M500 S`, consultas a `M503 S V`/`M503 S R` e escrita de versão a `M1004`. No fonte, `src/core/commands/gcode/composer/m1003_m1009.h:51` atribui esse parâmetro a `printerVersion`; M1006 o imprime e M1007 imprime a versão de build. Portanto `VER:1.0.4nw` não identifica, por si, o executável MCU.

Proveniência REA, inspeção sem execução do gravador:

- Metadados: `ev_e08c77604c0a1eda28b48b0456ca5c2f00065e72c1a7950b27b1d72b92066968`.
- Membros/CIL: `ev_8a8e5489f6cf2bc6875189e998ab955c48050f79f96a67d2bdbc202c11dc2cc2`.
- Strings: `ev_ba4b64a238231783acad58f45868702491150a970e5f74639a573c5f96158505`.
- `Flasher.dll`: SHA-256 `b1988a7fa7ebbd8b5f0530f70eda3315e306f15b889121d15ae68a1ae7cce8af`; MVID `512cf389-7532-4956-8f7d-f6b80b4115c6`.

Os IDs referem-se à evidência da sessão; não se afirma existir exportação completa em arquivo. Não houve descompilação ARM nem leitura da Flash do equipamento. As conclusões sobre o caminho de movimento e restauração vêm do fonte e da comparação com logs, não de execução instrumentada.

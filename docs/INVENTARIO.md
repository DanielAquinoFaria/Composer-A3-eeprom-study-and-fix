# Inventário, versões e finalidade

## Caminho mínimo para reproduzir a solução

| Item | Caminho relativo à raiz | Estado |
|---|---|---|
| Imagem confirmada pelo operador | `gravador/imagens/AT24C256C_Composer_A3_1.0.5_MKA_sem_SN.bin` | 32.768 bytes; SHA-256 conferido |
| Interface de gravação | `gravador/desktop/app.py` e `eeprom.py` | Fonte Python/Tkinter completo |
| Dependência de execução | `gravador/requirements.txt` | pyserial 3.5 |
| Firmware Uno | `gravador/firmware/eeprom_uno/eeprom_uno.ino` | Fonte completo; usa Wire do core AVR |
| Firmware Uno compilado | `gravador/firmware/precompilado/eeprom_uno.hex` | Uno R3/ATmega328P, 16 MHz, sem bootloader |
| Esquemáticos | `gravador/hardware/` | SVG, PNG, HTML e montagem fio por fio |
| Protocolo/testes | `gravador/PROTOCOLO.md`, `gravador/tests/` | 16 testes aprovados nesta entrega |

## Reconstrução da imagem

| Entrada/ferramenta | Local e versão |
|---|---|
| Fonte MKA | `gravador/dependencies/firmwares/firmware codigo fonte/MKA-firmware/`; revisão registrada `6e02973b1b8f325040cc3dbf66ac545ffc5c06b3`, identificação 1.2.7dev |
| Perfil | `gravador/dependencies/Composer Flasher/Composer A3/MKA_1.2.6_ComposerA3_v1.0.x_15-05-2024/Composer A3-1.0.5.gc` |
| Gerador | `gravador/tools/gerar_imagem_mka.py` |
| Comparador | `gravador/tools/comparar_dumps_mka.py` |
| Mapas/manifestos | `gravador/imagens/` — JSON, CSV e SHA-256 |
| Instruções de reprodução | `gravador/REPRODUZIR.md` |

O fonte MKA está disponível diretamente em `firmwares/MKA-firmware/` e também no caminho das dependências acima, para preservar o funcionamento do gerador e seus testes. Os 661 arquivos das duas cópias foram comparados por SHA-256 e são idênticos. Não há submódulo a baixar. O perfil tem também uma cópia dentro do pacote original do Flasher; os bytes foram conferidos entre as duas cópias.

## Firmwares e ferramentas históricos

`firmwares/Composer Flasher/` preserva **os 49 arquivos** do pacote local: `FlasherWin.exe`, assemblies, configurações, `bossac.exe`, bibliotecas nativas/runtime e pacotes A3/A4 compactados e extraídos. O arquivo de runtime declara .NET 8 e Windows Desktop 8. O runtime .NET não está embutido; deve ser instalado separadamente para executar essa aplicação Windows.

| Arquivo | Bytes | SHA-256 |
|---|---:|---|
| A3 / pacote 15-05-2024 / `MKA.bin` | 236720 | `aff23a70b3ade6c049ad2be86920a1c284bc802a2a35d914db181105dd700f6f` |
| A3 / `MKA_1.2.6_ComposerA3_v1.0.x_24-03-2022_2127.fw2` | 454846 | `58276ba214d8d170a6834205e469c86e313d6de44861b136130fd21140f30295` |
| A4 / pacote 15-05-2024 / `MKA.bin` | 237088 | `7d6f0778acc0f8d0edb886d5c95c75cef6d5f685e428f60d36bda4168e8d4d6f` |
| A4 / `MKA_1.2.6dev_ComposerA4_v1.0.x_28-02-2022_1809.fw2` | 458239 | `c85c232249b86e761a92e78ecb2958cd170eb7522a6918c1c2ba61f70933f916` |

O A4 permanece apenas para preservar o pacote recebido. Não aplicar seus arquivos na A3. Datas dos nomes de pacotes não são prova de recompilação dos executáveis.

`firmwares/MK4duo/` é o snapshot de referência local, revisão `0d8ee93b259bdfb2fb36487488f15d7e27ffb950`, com fonte, documentação, fontes gráficas e arquivos Nextion disponíveis. O repositório original estava sem alterações reportadas por `git status --porcelain`. É contexto histórico, não um firmware substituto validado para a Composer A3.

## Evidências e referências

- `evidencias/logs/`: logs originais e G-codes de teste disponíveis. Os G-codes são registros de contexto; não foram validados como procedimento universal de ensaio.
- `evidencias/dossie_inicial.md` e `diagnostico_2026-10-30.md`: documentos anteriores, com avisos de contexto e links adaptados.
- `evidencias/leitor_esp32c3/`: leitor anterior, coletor Python e 14 testes; nenhum firmware ESP32 deve ser enviado ao Uno ou à controladora.
- `gravador/imagens/clones/`: seis dumps de 32.768 bytes, sem alteração.
- `referencias/datasheets/`: quatro PDFs locais, AT24C256C, SAM3X, Ultratronics e MAX31865.
- `referencias/Firmware Flashing Guide for Composer.docx`: guia recebido, copiado integralmente.

## Dependências externas

O pacote contém código-fonte, binários de aplicação/firmware e documentação disponíveis no projeto, mas não redistribui instalações de Python/Tk, Arduino IDE, cores AVR/ESP32, GCC, .NET ou pacotes pip instalados.

Para executar o gravador: Python 3.10+, Tcl/Tk e pyserial 3.5. Para carregar o sketch: Arduino IDE e Arduino AVR Boards 1.8.6. Para reconstruir a imagem a partir das macros: GNU Arm Embedded GCC 4.8.3-2014q1, conforme `gravador/REPRODUZIR.md`. Para redesenhar os esquemas: dependências de `requirements-dev.txt` e as fontes indicadas no script.

A compilação do Uno nesta entrega utilizou AVR Boards 1.8.6 e avr-gcc 7.3.0-atmel3.6.1-arduino7. O ambiente de testes foi Python 3.10.10, pyserial 3.5, Tk 8.6.

## Critérios de organização

Foram excluídos metadados `.git`, caches, objetos e diretórios de compilação intermediária. O HEX final do Uno foi preservado em `firmware/precompilado`. O projeto REA não é necessário para executar o gravador, gerar a imagem ou verificar os dumps e não foi copiado. Os arquivos de origem continuam no workspace.

`PROVENIENCIA.json` registra cada arquivo inicialmente copiado e seu hash de origem. Os ajustes editoriais em guias são listados nesse documento; `MANIFESTO_SHA256.json`, na raiz, registra a versão final de todos os arquivos entregues, exceto ele próprio.

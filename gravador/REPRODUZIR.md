# Executar e reproduzir

Execute os comandos dentro da pasta `gravador/` desta entrega. Não é necessário ter a antiga pasta
`anisoprintV2`, nem REA, nem outros repositórios ao lado deste clone.

## Interface e testes

Python 3.10+ com Tcl/Tk e pyserial 3.5:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python desktop/app.py
python -m unittest discover -s tests -v
```

Os testes incluem a interface simulada e exigem sessão gráfica com Tk. Não abrem
uma porta serial física. Para uso real, siga README.md e hardware/MONTAGEM.md.
O inicializador `iniciar.bat` usa o Python disponível no PATH.

## Firmware do gravador

Fonte: `firmware/eeprom_uno/eeprom_uno.ino`. No Arduino IDE, use Arduino AVR Boards
1.8.6, Arduino Uno, e carregue pela porta correspondente. O sketch usa a biblioteca
Wire do core. Para compilar sem upload no Windows:

```powershell
python tools/build_firmware.py
# Instalação alternativa:
python tools/build_firmware.py --arduino-packages "C:/caminho/packages/arduino"
```

O padrão é `%LOCALAPPDATA%/Arduino15/packages/arduino`; requer os subdiretórios
`hardware/avr` e `tools/avr-gcc`. Saída: `build/eeprom_uno.hex`, sem bootloader.
Os objetos e o build são regeneráveis e não são publicados.

## Imagem EEPROM MKA

Fontes exatas incluídas em `dependencies/firmwares/firmware codigo fonte/MKA-firmware`.
Perfil incluído em `dependencies/Composer Flasher/Composer A3/MKA_1.2.6_ComposerA3_v1.0.x_15-05-2024/Composer A3-1.0.5.gc`.
O gerador resolve ambos relativamente ao próprio arquivo, sem depender do diretório pai.

É necessário GNU Arm Embedded GCC 4.8.3-2014q1 para Windows, com
`arm-none-eabi-g++.exe` e `arm-none-eabi-objcopy.exe` no diretório bin.
A instalação local validada foi a distribuída com Sloeber em
`C:/sloeber/Sloeber/arduinoPlugin/packages/arduino/tools/arm-none-eabi-gcc/4.8.3-2014q1/bin`.
O compilador não está incluído. Outra instalação pode ser indicada explicitamente:

```powershell
python tools/gerar_imagem_mka.py --toolchain "C:/caminho/arm-none-eabi-gcc/bin"
python -m unittest discover -s tests -v
python tools/comparar_dumps_mka.py
```

Saídas: `.bin`, `.json`, `.sha256` e `_mapa.csv` em `imagens/`.
A imagem de 32768 bytes deve ter SHA-256
`a54501351980aeef05636856efa92e8a668bbfaf2794a42b80f438af59d0dc1e`.
Os caminhos no manifesto JSON são relativos a `dependencies/`.
Os testes do arquivo pronto não exigem ARM GCC. O comparador lê os seis dumps
em `imagens/clones/` e reescreve os relatórios de comparação; não altera os dumps.

## Esquemáticos

Os PNG/SVG/HTML prontos estão em `hardware/`. Para regenerar no Windows:

```powershell
python -m pip install -r requirements-dev.txt
python tools/desenhar_esquematico.py
```

O script usa Pillow e as fontes locais `C:/Windows/Fonts/segoeui.ttf` e
`segoeuib.ttf`. As fontes Windows não são redistribuídas. Outros sistemas precisam
adaptar esses caminhos. O gravador não depende de Pillow.

## Validação desta publicação — 04/11/2026

16 testes passaram, incluindo GUI simulada, integridade das fontes, CRCs e imagem.
A regeneração pelo ARM GCC manteve o hash acima. O firmware Uno compilou:
8466 bytes de programa e 721 bytes de RAM. Não houve upload, gravação física
ou teste de movimento da impressora nesta publicação.

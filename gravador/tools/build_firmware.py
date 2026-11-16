"""Build using an already installed Arduino AVR core and avr-gcc (no upload)."""
import argparse
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--arduino-packages', type=Path, default=Path(os.environ.get('LOCALAPPDATA', '')) / 'Arduino15/packages/arduino')
args = parser.parse_args()
root = Path(__file__).resolve().parents[1]
core_package = sorted((args.arduino_packages / 'hardware/avr').iterdir())[-1]
toolchain = sorted((args.arduino_packages / 'tools/avr-gcc').iterdir())[-1] / 'bin'
core = core_package / 'cores/arduino'
wire = core_package / 'libraries/Wire/src'
build = root / 'build'
build.mkdir(exist_ok=True)
includes = [f'-I{p}' for p in (core, core_package / 'variants/standard', wire)]
flags = ['-Os', '-g', '-ffunction-sections', '-fdata-sections', '-flto', '-mmcu=atmega328p', '-DF_CPU=16000000L', '-DARDUINO=10819', '-DARDUINO_AVR_UNO', '-DARDUINO_ARCH_AVR']
sources = sorted(core.glob('*.c')) + sorted(core.glob('*.cpp')) + sorted(core.glob('*.S')) + sorted(wire.glob('*.cpp')) + sorted((wire / 'utility').glob('*.c'))
sketch = build / 'eeprom_uno.cpp'
sketch.write_text('#include <Arduino.h>\n' + (root / 'firmware/eeprom_uno/eeprom_uno.ino').read_text(encoding='utf-8-sig'), encoding='utf-8')
sources.append(sketch)
objects = []
for i, source in enumerate(sources):
    cpp = source.suffix == '.cpp'
    compiler = toolchain / ('avr-g++.exe' if cpp else 'avr-gcc.exe')
    extra = ['-std=gnu++11', '-fno-exceptions', '-fno-threadsafe-statics'] if cpp else ['-std=gnu11'] if source.suffix == '.c' else ['-x', 'assembler-with-cpp']
    obj = build / f'{i}_{source.stem}.o'
    subprocess.run([str(compiler), *flags, *extra, *includes, '-c', str(source), '-o', str(obj)], check=True)
    objects.append(str(obj))
elf = build / 'eeprom_uno.elf'
subprocess.run([str(toolchain / 'avr-gcc.exe'), *flags, '-Wl,--gc-sections', '-o', str(elf), *objects, '-lm'], check=True)
subprocess.run([str(toolchain / 'avr-objcopy.exe'), '-O', 'ihex', '-R', '.eeprom', str(elf), str(build / 'eeprom_uno.hex')], check=True)
subprocess.run([str(toolchain / 'avr-size.exe'), '-C', '--mcu=atmega328p', str(elf)], check=True)
print('Firmware compilado:', build / 'eeprom_uno.hex')

"""Generate a complete AT24C256C image from MKA defaults + Composer A3-1.0.5.gc.
No serial access. ARM compilation evaluates the original configuration macros.
"""
import argparse
import binascii
import csv
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess

PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / 'dependencies'
SOURCE = ROOT / 'firmwares/firmware codigo fonte/MKA-firmware'
PROFILE = ROOT / 'Composer Flasher/Composer A3/MKA_1.2.6_ComposerA3_v1.0.x_15-05-2024/Composer A3-1.0.5.gc'
DEFAULT_TOOLCHAIN = Path('C:/sloeber/Sloeber/arduinoPlugin/packages/arduino/tools/arm-none-eabi-gcc/4.8.3-2014q1/bin')
TYPES = {'f': 'float', 'I': 'uint32_t', 'H': 'uint16_t', 'h': 'int16_t', 'B': 'uint8_t', 'b': 'int8_t', '?': 'bool', '3x': 'uint8_t'}


def schema():
    fields = []
    def add(block, name, fmt, expression, origin='MKA defaults / Factory_Settings'):
        fields.append(dict(block=block, name=name, fmt=fmt, expression=expression, origin=origin))
    def u(name, fmt, expr, origin='MKA defaults / Factory_Settings'):
        add('USER', name, fmt, expr, origin)
    def s(name, fmt, expr):
        add('SYSTEM', name, fmt, expr)
    for i, axis in enumerate('EUV', 3):
        u(f'steps_{axis}', 'f', f'steps[{i}]')
    for axis in 'XYZ':
        u(f'home_{axis}', 'f', '0')
    for axis in 'XYZ':
        for h in range(2):
            u(f'hotend_{h}_{axis}', 'f', f'offset_{axis}[{h}]')
    for axis in 'XY':
        u(f'switch_offset_{axis}', 'f', '0', 'src/core/tools/tools.cpp: inicialização estática')
    u('preheat_hotend', 'H', 'PREHEAT_1_TEMP_HOTEND', 'NextionHMI.cpp / Configuration_Temperature.h')
    u('preheat_bed', 'H', 'PREHEAT_1_TEMP_BED', 'NextionHMI.cpp / Configuration_Temperature.h')
    u('lcd_brightness', 'B', '90', 'NextionHMI.cpp: inicialização estática')
    for h in range(4):
        for term in ('Kp', 'Ki', 'Kd'):
            expr = f'{term}[{h}]' if h < 2 else f'DEFAULT_{"bed" if h == 2 else "chamber"}{term}'
            u(f'heater_{h}_{term}', 'f', expr)
    for axis, macro in zip('XYZEUV', ('X', 'Y', 'Z', 'E0', 'E1', 'E2')):
        s(f'dir_{axis}', '?', f'INVERT_{macro}_DIR')
    for i, axis in enumerate('XYZ'):
        s(f'steps_{axis}', 'f', f'steps[{i}]')
    for name, array, fmt in [('feedrate', 'feedrate', 'f'), ('max_accel', 'max_accel', 'I')]:
        for i, axis in enumerate('XYZEUV'):
            s(f'{name}_{axis}', fmt, f'{array}[{i}]')
    s('acceleration', 'f', 'DEFAULT_ACCELERATION')
    for i, axis in enumerate('EUV'):
        s(f'retract_accel_{axis}', 'f', f'retract_accel[{i}]')
    for name, fmt, expr in [('travel_acceleration','f','DEFAULT_TRAVEL_ACCELERATION'), ('min_feedrate','f','DEFAULT_MINIMUMFEEDRATE'), ('min_travel_feedrate','f','DEFAULT_MINTRAVELFEEDRATE'), ('min_segment_us','I','DEFAULT_MINSEGMENTTIME')]:
        s(name, fmt, expr)
    for i, axis in enumerate('XYZEUV'):
        s(f'jerk_{axis}', 'f', f'DEFAULT_{axis}JERK' if i < 3 else f'ejerk[{i-3}]')
    logic = ['X_MIN_ENDSTOP_LOGIC','Y_MIN_ENDSTOP_LOGIC','Z_MIN_ENDSTOP_LOGIC','Z_PROBE_ENDSTOP_LOGIC','X_MAX_ENDSTOP_LOGIC','Y_MAX_ENDSTOP_LOGIC','Z_MAX_ENDSTOP_LOGIC','X2_MIN_ENDSTOP_LOGIC','X2_MAX_ENDSTOP_LOGIC','Y2_MIN_ENDSTOP_LOGIC','Y2_MAX_ENDSTOP_LOGIC','Z2_MIN_ENDSTOP_LOGIC','Z2_MAX_ENDSTOP_LOGIC','FIL_RUNOUT_LOGIC','DOOR_OPEN_LOGIC','POWER_CHECK_LOGIC']
    pull = ['ENDSTOPPULLUP_XMIN','ENDSTOPPULLUP_YMIN','ENDSTOPPULLUP_ZMIN','ENDSTOPPULLUP_ZPROBE','ENDSTOPPULLUP_XMAX','ENDSTOPPULLUP_YMAX','ENDSTOPPULLUP_ZMAX','ENDSTOPPULLUP_X2MIN','ENDSTOPPULLUP_X2MAX','ENDSTOPPULLUP_Y2MIN','ENDSTOPPULLUP_Y2MAX','ENDSTOPPULLUP_Z2MIN','ENDSTOPPULLUP_Z2MAX','PULLUP_FIL_RUNOUT','PULLUP_DOOR_OPEN','PULLUP_POWER_CHECK']
    for name, macros in [('endstop_logic', logic), ('endstop_pullup', pull)]:
        s(name, 'H', ' | '.join(f'((uint16_t)({macro}) << {i})' for i, macro in enumerate(macros)))
    for h in range(4):
        hot = h < 2
        prefix = '' if hot else ('BED_' if h == 2 else 'CHAMBER_')
        pin = str(h) if hot else ('BED' if h == 2 else 'CHAMBER')
        therm = f'HOT{h}' if hot else pin
        pid = 'PIDTEMP' if hot else 'PIDTEMP' + pin
        inverted = 'INVERTED_HEATER_PINS' if hot else f'INVERTED_{pin}_PIN'
        values = [('type','B',str(0 if hot else h-1)), ('pin','b',f'HEATER_{pin}_PIN'), ('id','B',str(h)), ('pid_min','B',prefix+'PID_DRIVE_MIN'), ('pid_max_drive','B',prefix+'PID_DRIVE_MAX'), ('pid_max','B',prefix+'PID_MAX'), ('min_temp','h',f'HEATER_{h}_MINTEMP' if hot else prefix+'MINTEMP'), ('max_temp','h',f'HEATER_{h}_MAXTEMP' if hot else prefix+'MAXTEMP'), ('Kc','f',f'Kc[{h}]' if hot else '0'), ('flags','B',f'({pid} ? 1 : 0) | 2 | ({inverted} ? 4 : 0)'), ('sensor_pin','b',f'TEMP_{pin}_PIN'), ('sensor_type','h',f'TEMP_SENSOR_{pin}'), ('adc_low','h','0'), ('adc_high','h','0'), ('r25','f',therm+'_R25'), ('beta','f',therm+'_BETA'), ('pullup','f','THERMISTOR_SERIES_RS'), ('shC','f','0')]
        for name, fmt, expr in values:
            s(f'heater_{h}_{name}', fmt, expr)
    for fan in range(4):
        for name, fmt, expr in [('pin','b',f'fan_pins[{fan}]'), ('freq','H','250'), ('min','B','FAN_MIN_PWM'), ('auto','b',f'auto_fan[{fan}]'), ('flags','B','FAN_INVERTED ? 1 : 0')]:
            s(f'fan_{fan}_{name}', fmt, expr)
    s('linear_advance', 'f', 'LIN_ADVANCE_K')
    for label in ('load', 'unload'):
        for i in range(3):
            s(f'{label}_{i}', 'f', f'{label}[{i}]')
    for name, macro in [('pause_retract','RETRACT_LENGTH'), ('pause_retract_feed','RETRACT_FEEDRATE'), ('pause_load_feed','LOAD_FEEDRATE'), ('pause_unload_feed','UNLOAD_FEEDRATE'), ('pause_extrude_feed','EXTRUDE_FEEDRATE')]:
        s(name, 'f', 'PAUSE_PARK_' + macro)
    for name, macro in [('cut_servo','CUT_SERVO_ID'), ('cut_active','CUT_ACTIVE_ANGLE'), ('cut_neutral','CUT_NEUTRAL_ANGLE')]:
        s(name, 'B', macro)
    for tool in range(2):
        for step in range(12):
            for name, fmt in [('X','f'), ('Y','f'), ('Speed','f'), ('SwitchMove','?')]:
                s(f'path_{tool}_{step}_{name}', fmt, f'path{tool}[{step}].{name}')
            s(f'path_{tool}_{step}_padding', '3x', '{0,0,0}')
    for slot in range(2):
        for name, fmt, expr in [('pin','b',f'SD{slot}_SS_PIN'), ('detect','b','SD_DETECT_PIN'), ('divisor','B',f'SD{slot}_SPEED_DIVISOR')]:
            s(f'sd_{slot}_{name}', fmt, expr)
    return fields


def extract_defaults(fields, toolchain):
    build = PROJECT / 'tools/mka_build'
    build.mkdir(exist_ok=True)
    includes = ['src/lib/macros.h','Boards.h','Configuration_Basic.h','Configuration_Core.h','Configuration_Temperature.h','Configuration_Feature.h','src/lib/conditionals_pre.h','src/lib/pins.h','src/lib/conditionals_post.h','src/core/heater/sensor/thermistor.h']
    cpp = '#include <stdint.h>\n#include <stddef.h>\n' + ''.join(f'#include "{p}"\n' for p in includes)
    # Copy the exact source declarations, including the ARM enum and structure ABI.
    heater_header = (SOURCE / 'src/core/heater/heater.h').read_text(encoding='utf-8', errors='replace')
    tools_header = (SOURCE / 'src/core/tools/tools.h').read_text(encoding='utf-8', errors='replace')
    cpp += re.search(r'typedef enum \{ IS_HOTEND.*?Heater_type;', heater_header).group() + '\n'
    cpp += re.search(r'struct ToolSwitchPos\s*\{.*?\};', tools_header, re.S).group() + '\n'
    cpp += '''
static_assert(sizeof(Heater_type)==1, "ARM enum width");
static_assert(sizeof(ToolSwitchPos)==16 && offsetof(ToolSwitchPos,SwitchMove)==12, "tool path ABI");
static_assert(sizeof(float)==4 && sizeof(bool)==1, "scalar ABI");
static_assert(HEATER_COUNT==4 && FAN_COUNT==4 && DRIVER_EXTRUDERS==3 && HOTENDS==2 && SD_COUNT==2, "A3 feature set");
#if HEATER_USES_AD595
#error Unsupported AD595 layout
#endif
constexpr float steps[] = DEFAULT_AXIS_STEPS_PER_UNIT;
constexpr float feedrate[] = DEFAULT_MAX_FEEDRATE;
constexpr uint32_t max_accel[] = DEFAULT_MAX_ACCELERATION;
constexpr uint32_t retract_accel[] = DEFAULT_RETRACT_ACCELERATION;
constexpr float ejerk[] = DEFAULT_EJERK;
constexpr float offset_X[] = HOTEND_OFFSET_X;
constexpr float offset_Y[] = HOTEND_OFFSET_Y;
constexpr float offset_Z[] = HOTEND_OFFSET_Z;
constexpr float Kp[] = DEFAULT_Kp;
constexpr float Ki[] = DEFAULT_Ki;
constexpr float Kd[] = DEFAULT_Kd;
constexpr float Kc[] = DEFAULT_Kc;
constexpr int8_t fan_pins[] = FANS_CHANNELS;
constexpr int8_t auto_fan[] = AUTO_FAN;
constexpr float load[] = PAUSE_PARK_LOAD_LENGTH;
constexpr float unload[] = PAUSE_PARK_UNLOAD_LENGTH;
constexpr ToolSwitchPos path0[] = CHANGE_T0;
constexpr ToolSwitchPos path1[] = CHANGE_T1;
struct __attribute__((packed)) Defaults {
'''
    for field in fields:
        suffix = '[3]' if field['fmt'] == '3x' else ''
        cpp += f"  {TYPES[field['fmt']]} {field['name']}{suffix};\n"
    cpp += '};\nstatic_assert(sizeof(Defaults)==852, "USER and SYSTEM payload sizes");\n'
    cpp += 'extern const Defaults defaults __attribute__((section(".eeprom_defaults"),used)) = {\n'
    cpp += ',\n'.join(f"  {field['expression']}" for field in fields) + '\n};\n'
    (build / 'defaults.cpp').write_text(cpp, encoding='utf-8')
    subprocess.run([str(toolchain/'arm-none-eabi-g++.exe'), '-std=gnu++11', '-mcpu=cortex-m3', '-mthumb', '-DARDUINO_ARCH_SAM', '-D__SAM3X8E__', f'-I{SOURCE}', f'-I{SOURCE}/config/COMPOSER_A3_V10', '-c', str(build/'defaults.cpp'), '-o', str(build/'defaults.o')], check=True)
    subprocess.run([str(toolchain/'arm-none-eabi-objcopy.exe'), '-O', 'binary', '-j', '.eeprom_defaults', str(build/'defaults.o'), str(build/'defaults.raw')], check=True)
    raw = (build/'defaults.raw').read_bytes()
    if len(raw) != 852:
        raise ValueError(f'Unexpected payload size {len(raw)}')
    pos = 0
    for field in fields:
        n = struct.calcsize('<' + field['fmt'])
        field['value'] = None if field['fmt'] == '3x' else struct.unpack_from('<' + field['fmt'], raw, pos)[0]
        field['default'] = field['value']
        pos += n
    assert pos == len(raw)


def apply_profile(fields):
    lookup = {field['name']: field for field in fields}
    consumed = []
    for line_number, line in enumerate(PROFILE.read_text(encoding='utf-8-sig').splitlines(), 1):
        line = line.split(';', 1)[0].strip()
        if not line:
            continue
        words = line.split()
        command = words[0]
        args = {word[0]: float(word[1:]) for word in words[1:]}
        handled = set()
        def set_field(key, name, bit=None):
            if key not in args:
                return
            field = lookup[name]
            value = args[key]
            if bit is not None:
                value = (int(field['value']) & ~(1 << bit)) | (int(bool(value)) << bit)
            if field['fmt'] != 'f':
                if value != int(value):
                    raise ValueError(f'Noninteger {name}')
                value = bool(value) if field['fmt'] == '?' else int(value)
            # Round through the actual on-disk scalar type and enforce representable range.
            field['value'] = struct.unpack('<'+field['fmt'], struct.pack('<'+field['fmt'], value))[0]
            field['origin'] = f'{PROFILE.name}:{line_number}: {line}'
            handled.add(key)
        if command in ('M569','M92','M203','M201'):
            prefix = {'M569':'dir','M92':'steps','M203':'feedrate','M201':'max_accel'}[command]
            for axis in 'XYZEUV':
                set_field(axis, f'{prefix}_{axis}')
        elif command == 'M204':
            for key, name in [('P','acceleration'), ('T','travel_acceleration')]+[(a,f'retract_accel_{a}') for a in 'EUV']:
                set_field(key, name)
        elif command == 'M205':
            for key, name in [('S','min_feedrate'),('T','min_travel_feedrate'),('B','min_segment_us')]+[(a,f'jerk_{a}') for a in 'XYZEUV']:
                set_field(key, name)
        elif command in ('M305','M306'):
            h = {0:0, 1:1, -1:2, -2:3}[args['H']]
            handled.add('H')
            mapping = {'P':'sensor_pin','S':'sensor_type','A':'r25','B':'beta','C':'shC','R':'pullup','L':'adc_low','O':'adc_high'} if command == 'M305' else {'P':'pin','A':'pid_min','B':'pid_max_drive','C':'pid_max','L':'min_temp','O':'max_temp'}
            for key, name in mapping.items():
                set_field(key, f'heater_{h}_{name}')
            if command == 'M306':
                set_field('U', f'heater_{h}_flags', 0)
                set_field('I', f'heater_{h}_flags', 2)
        elif command == 'M106':
            fan = int(args['P']); handled.add('P')
            for key, name in {'U':'pin','L':'min','F':'freq','H':'auto'}.items():
                set_field(key, f'fan_{fan}_{name}')
            set_field('I', f'fan_{fan}_flags', 0)
        elif command == 'M900':
            set_field('K','linear_advance')
        elif command == 'M704':
            if 'E' in args:
                driver = int(args['E']); handled.add('E')
                set_field('L', f'load_{driver}')
                set_field('U', f'unload_{driver}')
            for key,name in {'A':'pause_retract','B':'pause_retract_feed','C':'pause_load_feed','D':'pause_unload_feed','K':'pause_extrude_feed'}.items():
                set_field(key, name)
        elif command == 'M1011':
            for key,name in {'S':'cut_servo','A':'cut_active','B':'cut_neutral'}.items():
                set_field(key, name)
        elif command == 'M217':
            tool, step = int(args['T']), int(args['S']); handled.update(('T','S'))
            for key,name in {'X':'X','Y':'Y','V':'Speed','K':'SwitchMove'}.items():
                set_field(key, f'path_{tool}_{step}_{name}')
        elif command == 'M39':
            slot = int(args['P']); handled.add('P')
            for key,name in {'U':'pin','D':'divisor','C':'detect'}.items():
                set_field(key, f'sd_{slot}_{name}')
        else:
            raise ValueError(f'Unsupported command at line {line_number}: {line}')
        if handled != set(args):
            raise ValueError(f'Unconsumed arguments at line {line_number}: {set(args)-handled}')
        consumed.append(dict(line=line_number, command=line, arguments_consumed=sorted(handled)))
    return consumed


def build_image(fields, serial_number='', printer_version='1.0.5'):
    image = bytearray(b'\xff' * 32768)
    blocks = []
    for block, start, version, length in [('USER',10,b'MKA12\0',117), ('SYSTEM',4106,b'SC12\0\0',751)]:
        pos = start + 8
        for field in fields:
            if field['block'] != block:
                continue
            field['offset'] = pos
            raw = struct.pack('<'+field['fmt'], *([] if field['fmt']=='3x' else [field['value']]))
            image[pos:pos+len(raw)] = raw
            field['size'] = len(raw)
            field['hex'] = raw.hex().upper()
            pos += len(raw)
        assert pos == start + length, (block, pos, start+length)
        crc = binascii.crc_hqx(image[start+8:pos], 0)
        image[start:start+8] = version + struct.pack('<H', crc)
        blocks.append(dict(name=block, start=start, length=length, payload_length=length-8, crc=crc, crc_hex=f'{crc:04X}'))
    for offset, size, text in [(32010,17,serial_number), (32027,9,printer_version)]:
        raw = text.encode('ascii')
        if len(raw) >= size or b'\0' in raw:
            raise ValueError('Identificação muito longa ou inválida')
        image[offset:offset+size] = raw.ljust(size,b'\0')
    return bytes(image), blocks


def crc_reference(data):
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            crc = ((crc << 1) ^ (0x1021 if crc & 0x8000 else 0)) & 0xffff
    return crc


def validate_image(image):
    assert len(image) == 32768
    assert image[10:16] == b'MKA12\0'
    assert image[4106:4112] == b'SC12\0\0'
    for start, length in [(10,117),(4106,751)]:
        assert struct.unpack_from('<H',image,start+6)[0] == crc_reference(image[start+8:start+length])
    assert image[32010:32027] == b'\0'*17
    assert image[32027:32036] == b'1.0.5\0\0\0\0'
    assert struct.unpack_from('<ff',image,66) == (0,0)
    assert struct.unpack_from('<HHB',image,74) == (230,60,90)
    assert image[4114:4120] == bytes([0,1,1,1,1,1])
    assert struct.unpack_from('<3f',image,4120) == (100,100,2560)
    assert struct.unpack_from('<3f',image,4132) == (180,180,5)
    assert image[4851:4857] == bytes([62,255,21,255,255,8])
    for start,end in [(0,10),(127,4106),(4857,32010),(32036,32768)]:
        assert image[start:end] == b'\xff'*(end-start)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--toolchain',type=Path,default=DEFAULT_TOOLCHAIN)
    args = parser.parse_args()
    fields = schema()
    extract_defaults(fields,args.toolchain)
    consumed = apply_profile(fields)
    image, blocks = build_image(fields)
    validate_image(image)
    out = PROJECT/'imagens'
    out.mkdir(exist_ok=True)
    name = 'AT24C256C_Composer_A3_1.0.5_MKA_sem_SN'
    target = out/(name+'.bin')
    target.write_bytes(image)
    validate_image(target.read_bytes())
    source_files = [PROFILE, SOURCE/'src/core/eeprom/eeprom.cpp', SOURCE/'src/core/heater/heater.h', SOURCE/'src/core/tools/tools.h', SOURCE/'src/platform/HAL_DUE/HAL_eeprom_Due.cpp', SOURCE/'src/platform/HAL_DUE/HAL_Due.h', SOURCE/'src/lcd/nextion_hmi/NextionHMI.cpp', *sorted((SOURCE/'config/COMPOSER_A3_V10').glob('*.h'))]
    report = dict(image=target.name, size=len(image), sha256=hashlib.sha256(image).hexdigest(), profile=str(PROFILE.relative_to(ROOT)), source_version=(SOURCE/'Configuration_Version.h').read_text().split('SHORT_BUILD_VERSION ')[1].splitlines()[0], serial_number='', printer_version='1.0.5', fill='FF', blocks=blocks, commands=consumed, fields=fields, sources=[dict(path=str(p.relative_to(ROOT)), sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in source_files])
    (out/(name+'.json')).write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    with (out/(name+'_mapa.csv')).open('w',newline='',encoding='utf-8-sig') as stream:
        writer = csv.writer(stream,delimiter=';')
        writer.writerow(['bloco','endereco_hex','endereco_decimal','bytes','campo','tipo','valor','hex','origem'])
        for field in fields:
            writer.writerow([field['block'],f"0x{field['offset']:04X}",field['offset'],field['size'],field['name'],field['fmt'],field['value'],field['hex'],field['origin']])
    (out/(name+'.sha256')).write_text(f"{report['sha256']}  {target.name}\n",encoding='ascii')
    print(json.dumps({key:report[key] for key in ('image','size','sha256','blocks')},indent=2))
    print(f'{len(consumed)} comandos do perfil consumidos integralmente; {len(fields)} campos/paddings mapeados.')


if __name__ == '__main__':
    main()

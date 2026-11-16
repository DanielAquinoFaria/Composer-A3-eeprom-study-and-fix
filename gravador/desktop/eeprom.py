"""Serial protocol and EEPROM operations, independent of the GUI."""
import binascii
import time

SIZE = 32768
BLOCK = 30
PAGE = 64


class DeviceError(Exception):
    pass


class Cancelled(Exception):
    pass


def frame(body):
    raw = body.encode('ascii')
    return raw + f'*{binascii.crc_hqx(raw, 0xffff):04X}\n'.encode('ascii')


def unframe(raw):
    try:
        if not raw.endswith(b'\n') or len(raw) > 160:
            raise ValueError()
        body, crc = raw.rstrip(b'\r\n').rsplit(b'*', 1)
        if len(crc) != 4 or int(crc, 16) != binascii.crc_hqx(body, 0xffff):
            raise ValueError()
        return body.decode('ascii')
    except (ValueError, UnicodeError):
        raise DeviceError('Resposta serial inválida ou CRC incorreto. Reconecte.') from None


def validate_range(start, length):
    if start < 0 or length <= 0 or start + length > SIZE:
        raise ValueError('Faixa inválida: use endereços 0 a 32767, sem exceder 32768 bytes.')


def chunks(start, length):
    validate_range(start, length)
    offset = 0
    while offset < length:
        n = min(BLOCK, PAGE - (start + offset) % PAGE, length - offset)
        yield start + offset, offset, n
        offset += n


class SerialDevice:
    def __init__(self, port, address=0x50, transport=None):
        if not 0x50 <= address <= 0x57:
            raise ValueError('Endereço I2C deve estar entre 0x50 e 0x57.')
        self.address, self.seq = address, 0
        if transport is None:
            import serial
            self.serial = serial.Serial(port, 115200, timeout=2, write_timeout=2)
        else:
            self.serial = transport
        try:
            if transport is None:
                time.sleep(2.2)  # Uno resets when the serial port opens.
                self.serial.reset_input_buffer()
            if self.request('HELLO') != 'EEPROM_UNO_V1':
                raise DeviceError('Firmware incompatível; carregue eeprom_uno.ino.')
            if self.request(f'PROBE {address}') != 'PROBE':
                raise DeviceError('Resposta de detecção inválida.')
        except Exception:
            self.close()
            raise

    def close(self):
        self.serial.close()

    def request(self, command):
        self.seq = self.seq % 65535 + 1
        try:
            packet = frame(f'{self.seq} {command}')
            if self.serial.write(packet) != len(packet):
                raise DeviceError('Envio serial incompleto.')
            raw = self.serial.read_until(b'\n', 160)
            if not raw:
                raise DeviceError('Arduino não respondeu. Confira firmware e porta serial.')
            fields = unframe(raw).split(' ', 2)
            if len(fields) != 3 or fields[0] != str(self.seq):
                raise DeviceError('Resposta fora de sequência; reconecte.')
            if fields[1] != 'OK':
                raise DeviceError(f'Arduino: {fields[2]}. Confira conexões, endereço I2C e WP.')
            return fields[2]
        except Exception:
            # Never retry a write with an unknown outcome or reuse a desynchronized link.
            self.close()
            raise

    def read_block(self, address, n):
        result = self.request(f'READ {self.address} {address} {n}')
        try:
            data = bytes.fromhex(result)
            if len(data) != n:
                raise ValueError()
            return data
        except ValueError:
            self.close()
            raise DeviceError('Tamanho/conteúdo de leitura inválido.') from None

    def write_block(self, address, data):
        result = self.request(f'WRITE {self.address} {address} {len(data)} {data.hex().upper()}')
        if result != 'WRITTEN':
            self.close()
            raise DeviceError('Gravação não confirmada.')


class SimulatedDevice:
    """Volatile memory. Deliberately no serial or hardware side effects."""
    def __init__(self):
        self.memory = bytearray([0xff]) * SIZE

    def close(self):
        pass

    def read_block(self, address, n):
        time.sleep(0.001)
        return bytes(self.memory[address:address+n])

    def write_block(self, address, data):
        time.sleep(0.002)
        self.memory[address:address+len(data)] = data


def read_memory(device, start, length, progress=lambda *_: None, cancel=lambda: False):
    data = bytearray()
    for address, offset, n in chunks(start, length):
        if cancel():
            raise Cancelled('Leitura cancelada; nenhum arquivo foi salvo.')
        data.extend(device.read_block(address, n))
        progress(offset + n, length)
    return bytes(data)


def verify_memory(device, start, data, progress=lambda *_: None, cancel=lambda: False):
    for address, offset, n in chunks(start, len(data)):
        if cancel():
            raise Cancelled('Verificação cancelada.')
        actual = device.read_block(address, n)
        expected = data[offset:offset+n]
        if actual != expected:
            for i, (a, b) in enumerate(zip(actual, expected)):
                if a != b:
                    raise DeviceError(f'Divergência em 0x{address+i:04X}: lido {a:02X}, esperado {b:02X}.')
            raise DeviceError('Leitura incompleta durante a verificação.')
        progress(offset + n, len(data))


def write_memory(device, start, data, progress=lambda *_: None, cancel=lambda: False):
    for address, offset, n in chunks(start, len(data)):
        if cancel():
            raise Cancelled(f'Gravação cancelada após {offset} bytes. Memória parcialmente alterada.')
        device.write_block(address, data[offset:offset+n])
        progress(offset + n, len(data))
    # Firmware verifies every block; this second pass verifies the complete selected range.
    verify_memory(device, start, data, lambda done, total: progress(total + done, 2*total), cancel)

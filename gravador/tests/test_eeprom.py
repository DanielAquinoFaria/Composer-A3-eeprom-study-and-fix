import binascii
from pathlib import Path
import sys
import tempfile
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'desktop'))
from eeprom import (SIZE, Cancelled, DeviceError, SerialDevice, SimulatedDevice,
                    chunks, frame, unframe, read_memory, write_memory, verify_memory)
from app import atomic_save


class FakeSerial:
    def __init__(self):
        self.closed = False
        self.memory = bytearray([255]) * SIZE
        self.bad_crc = False
        self.wrong_sequence = False
        self.silent = False
        self.fail_write = False
        self.writes = []

    def write(self, packet):
        parts = unframe(packet).split()
        seq, op = parts[:2]
        status, value = 'OK', ''
        if op == 'HELLO':
            value = 'EEPROM_UNO_V1'
        elif op == 'PROBE':
            value = 'PROBE'
        else:
            address, n = map(int, parts[3:5])
            if op == 'READ':
                value = self.memory[address:address+n].hex()
            else:
                self.writes.append((address, n))
                if self.fail_write:
                    status, value = 'ERR', 'VERIFY'
                else:
                    self.memory[address:address+n] = bytes.fromhex(parts[5])
                    value = 'WRITTEN'
        if self.wrong_sequence:
            seq = '0'
        self.response = frame(f'{seq} {status} {value}')
        if self.bad_crc:
            self.response = self.response[:-5] + b'0000\n'
        return len(packet)

    def read_until(self, *_):
        return b'' if self.silent else self.response

    def close(self):
        self.closed = True


class Tests(unittest.TestCase):
    def test_crc_known_vector(self):
        self.assertEqual(binascii.crc_hqx(b'123456789', 65535), 0x29B1)
        self.assertEqual(unframe(frame('1 HELLO')), '1 HELLO')
        for bad in (b'', b'1 OK x*abcd\n', b'1 OK x*1234', b'garbage\n'):
            with self.assertRaises(DeviceError):
                unframe(bad)

    def test_page_and_wire_boundaries(self):
        for start in range(128):
            blocks = list(chunks(start, 513))
            self.assertEqual(sum(n for _, _, n in blocks), 513)
            for addr, offset, n in blocks:
                self.assertEqual(addr, start + offset)
                self.assertLessEqual(n, 30)
                self.assertLessEqual(addr % 64 + n, 64)
        self.assertEqual(list(chunks(32767, 1)), [(32767, 0, 1)])

    def test_invalid_ranges(self):
        for start, length in ((-1, 1), (0, 0), (0, -1), (32768, 1), (32767, 2), (0, 32769)):
            with self.assertRaises(ValueError):
                list(chunks(start, length))

    def test_full_memory_serial_roundtrip(self):
        wire = FakeSerial()
        device = SerialDevice('fake', transport=wire)
        data = bytes(range(256)) * 128
        write_memory(device, 0, data)
        self.assertEqual(read_memory(device, 0, SIZE), data)
        self.assertTrue(all(addr % 64 + n <= 64 and n <= 30 for addr, n in wire.writes))

    def test_partial_write_preserves_surroundings(self):
        wire = FakeSerial()
        device = SerialDevice('fake', transport=wire)
        data = bytes(range(100))
        write_memory(device, 63, data)
        self.assertEqual(wire.memory[:63], b'\xff'*63)
        self.assertEqual(wire.memory[63:163], data)
        self.assertEqual(wire.memory[163:], b'\xff'*(SIZE-163))

    def test_corrupt_or_missing_response_closes_link(self):
        for field in ('bad_crc', 'wrong_sequence', 'silent', 'fail_write'):
            wire = FakeSerial()
            device = SerialDevice('fake', transport=wire)
            setattr(wire, field, True)
            with self.assertRaises(DeviceError):
                device.write_block(0, b'abc')
            self.assertTrue(wire.closed)
            self.assertEqual(len(wire.writes), 1)  # No blind retry.

    def test_cancellation_at_block_boundary(self):
        wire = FakeSerial()
        device = SerialDevice('fake', transport=wire)
        stop = threading.Event()
        with self.assertRaises(Cancelled):
            write_memory(device, 0, b'\x01'*100, lambda *_: stop.set(), stop.is_set)
        self.assertEqual(wire.memory[:30], b'\x01'*30)
        self.assertEqual(wire.memory[30:100], b'\xff'*70)
        with self.assertRaises(Cancelled):
            read_memory(device, 0, 100, cancel=stop.is_set)

    def test_verification_reports_exact_address(self):
        wire = FakeSerial()
        device = SerialDevice('fake', transport=wire)
        with self.assertRaisesRegex(DeviceError, '0x0040'):
            verify_memory(device, 63, b'\xff\x00')

    def test_simulation_and_atomic_file(self):
        device = SimulatedDevice()
        write_memory(device, 32765, b'abc')
        self.assertEqual(read_memory(device, 32765, 3), b'abc')
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'backup.bin'
            atomic_save(path, b'old')
            atomic_save(path, b'new')
            self.assertEqual(path.read_bytes(), b'new')
            self.assertEqual(len(list(Path(folder).iterdir())), 1)


if __name__ == '__main__':
    unittest.main()

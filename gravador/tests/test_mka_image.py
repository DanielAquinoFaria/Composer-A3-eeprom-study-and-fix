"""Validate the delivered MKA image without hardware or an ARM compiler."""
import binascii
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tools'))
from gerar_imagem_mka import validate_image, apply_profile, build_image, PROFILE

NAME = 'AT24C256C_Composer_A3_1.0.5_MKA_sem_SN'


class MkaImageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.image = (ROOT/'imagens'/f'{NAME}.bin').read_bytes()
        cls.report = json.loads((ROOT/'imagens'/f'{NAME}.json').read_text(encoding='utf-8'))

    def test_complete_image_and_independent_crc(self):
        validate_image(self.image)
        self.assertEqual(len(self.image), 32768)
        self.assertEqual(binascii.crc_hqx(self.image[18:127], 0), 37164)
        # Independent historical evidence: accepted SYSTEM CRC in original boot logs.
        self.assertEqual(binascii.crc_hqx(self.image[4114:4857], 0), 13673)
        self.assertEqual(hashlib.sha256(self.image).hexdigest(), self.report['sha256'])

    def test_each_payload_bit_error_rejected(self):
        for start, end in [(18,127), (4114,4857)]:
            for pos in range(start,end):
                broken = bytearray(self.image)
                broken[pos] ^= 1
                with self.assertRaises(AssertionError):
                    validate_image(broken)

    def test_source_profile_replayed_without_unconsumed_arguments(self):
        fields = json.loads(json.dumps(self.report['fields']))
        for field in fields:
            field['value'] = field['default']
        consumed = apply_profile(fields)
        command_lines = [line for line in PROFILE.read_text(encoding='utf-8-sig').splitlines() if line.strip() and not line.startswith(';')]
        self.assertEqual(len(consumed), len(command_lines))
        image, blocks = build_image(fields)
        self.assertEqual(image, self.image)
        self.assertEqual(blocks, self.report['blocks'])

    def test_every_mapped_field_decodes_and_is_finite(self):
        occupied = set()
        for field in self.report['fields']:
            start, n = field['offset'], field['size']
            self.assertTrue(occupied.isdisjoint(range(start,start+n)))
            occupied.update(range(start,start+n))
            raw = self.image[start:start+n]
            self.assertEqual(raw.hex().upper(), field['hex'])
            if field['fmt'] == '3x':
                self.assertEqual(raw,b'\0'*3)
            else:
                value = struct.unpack('<'+field['fmt'],raw)[0]
                self.assertEqual(value,field['value'])
                if field['fmt'] == 'f':
                    self.assertTrue(math.isfinite(value))
        self.assertEqual(occupied, set(range(18,127)) | set(range(4114,4857)))

    def test_identity_and_user_defaults(self):
        self.assertEqual(self.image[32010:32027],b'\0'*17)
        self.assertEqual(self.image[32027:32036],b'1.0.5\0\0\0\0')
        self.assertEqual(struct.unpack_from('<ff',self.image,66),(0,0))
        self.assertEqual(struct.unpack_from('<HHB',self.image,74),(230,60,90))
        self.assertAlmostEqual(struct.unpack_from('<f',self.image,46)[0],-2.2,places=5)
        self.assertEqual(struct.unpack_from('<f',self.image,54)[0],-16.5)

    def test_input_sources_have_not_changed(self):
        for source in self.report['sources']:
            path = ROOT / 'dependencies' / source['path']
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),source['sha256'],source['path'])


if __name__ == '__main__':
    unittest.main()

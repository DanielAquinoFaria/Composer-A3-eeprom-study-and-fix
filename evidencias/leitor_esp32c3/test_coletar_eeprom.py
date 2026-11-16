"""Protocol and file-preservation tests. No serial port is opened or simulated."""

import binascii
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import io
import json
from pathlib import Path
import tempfile
import unittest

import coletar_eeprom as collector


def encoded_dump(data: bytes) -> bytes:
    lines = [collector.BEGIN]
    lines += [f"DATA {address:04X} {data[address:address + 16].hex().upper()}"
              for address in range(0, len(data), 16)]
    lines += [f"END_EEPROM_V1 SIZE=32768 CRC32={binascii.crc32(data) & 0xFFFFFFFF:08X}"]
    return ("\n".join(lines) + "\n").encode("ascii")


DATA = bytes(range(256)) * 128


def parse(raw: bytes) -> collector.DumpParser:
    parser = collector.DumpParser()
    for line in raw.splitlines(keepends=True):
        parser.feed(line)
    parser.finish()
    return parser


class ProtocolTests(unittest.TestCase):
    def test_valid_32k_dump_and_standard_crc(self):
        parser = parse((collector.INFO + "\r\n").encode() + encoded_dump(DATA))
        self.assertEqual(parser.finish(), DATA)
        self.assertEqual(parser.crc32, f"{binascii.crc32(DATA) & 0xFFFFFFFF:08X}")
        self.assertEqual(binascii.crc32(b"123456789"), 0xCBF43926)

    def test_changed_byte_rejected_by_crc(self):
        damaged = encoded_dump(DATA).replace(b"DATA 0000 00", b"DATA 0000 FF", 1)
        with self.assertRaisesRegex(collector.ProtocolError, "CRC32 mismatch"):
            parse(damaged)

    def test_duplicate_skipped_and_out_of_range_addresses(self):
        for replacement in (b"DATA 0000 ", b"DATA 0020 ", b"DATA 8000 "):
            with self.subTest(replacement=replacement):
                damaged = encoded_dump(DATA).replace(b"DATA 0010 ", replacement, 1)
                with self.assertRaisesRegex(collector.ProtocolError, "Address sequence"):
                    parse(damaged)

    def test_hex_length_and_non_hex_rejected(self):
        for replacement in (b"DATA 0000 0", b"DATA 0000 GG", b"DATA 0000 aa"):
            with self.subTest(replacement=replacement):
                damaged = encoded_dump(DATA).replace(b"DATA 0000 00", replacement, 1)
                with self.assertRaises(collector.ProtocolError):
                    parse(damaged)

    def test_missing_or_premature_end_and_wrong_size(self):
        raw = encoded_dump(DATA)
        for damaged in (raw.rsplit(b"END_", 1)[0],
                        raw.splitlines(keepends=True)[0] + raw.splitlines(keepends=True)[-1],
                        raw.replace(b"END_EEPROM_V1 SIZE=32768", b"END_EEPROM_V1 SIZE=32767")):
            with self.subTest(length=len(damaged)):
                with self.assertRaises(collector.ProtocolError):
                    parse(damaged)

    def test_error_aborts_including_before_begin(self):
        for raw in (b"ERROR I2C NACK\n", collector.BEGIN.encode() + b"\nERROR I2C timeout\n"):
            with self.assertRaisesRegex(collector.ProtocolError, "Reader reported"):
                parse(raw)

    def test_missing_begin_non_ascii_and_extra_data(self):
        for raw in (encoded_dump(DATA).split(b"\n", 1)[1],
                    b"\xff\n", encoded_dump(DATA) + b"DATA 0000 00000000000000000000000000000000\n"):
            with self.assertRaises(collector.ProtocolError):
                parse(raw)


class ArtifactTests(unittest.TestCase):
    def test_three_readings_manifest_and_comparison(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "arduino.log"
            other = bytes([DATA[0] ^ 1]) + DATA[1:]
            raw = collector.INFO.encode() + b"\n" + encoded_dump(DATA) * 2 + encoded_dump(other)
            source.write_bytes(raw)
            session = collector.Session(root / "dumps", "A", "offline_log")
            collector.convert_log(session, source)
            manifest_path = session.finish()
            manifest = json.loads(manifest_path.read_text(encoding="ascii"))
            self.assertEqual(manifest["valid_readings"], 3)
            self.assertEqual(manifest["status"], "comparison_mismatch")
            self.assertEqual(manifest["comparison"]["status"], "divergent")
            self.assertFalse(manifest["comparison"]["all_identical"])
            self.assertEqual([p["identical"] for p in manifest["comparison"]["pairs"]],
                             [True, False, False])
            self.assertEqual((session.path / "source.raw.log").read_bytes(), raw)
            self.assertEqual((session.path / "reading_001.bin").read_bytes(), DATA)
            self.assertEqual(manifest["readings"][0]["sha256"], hashlib.sha256(DATA).hexdigest())
            self.assertTrue(manifest["created_utc"].endswith("Z"))

    def test_failure_preserves_raw_and_partial_without_bin(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "failed.log"
            lines = encoded_dump(DATA).splitlines(keepends=True)
            raw = b"".join(lines[:3]) + b"ERROR I2C NACK\nremaining text\n"
            source.write_bytes(raw)
            session = collector.Session(root / "dumps", "B", "offline_log")
            with self.assertRaisesRegex(collector.ProtocolError, "Reader reported") as failure:
                collector.convert_log(session, source)
            session.finish(str(failure.exception))
            self.assertFalse(list(session.path.glob("*.bin")))
            self.assertEqual((session.path / "reading_001.partial").read_bytes(), DATA[:32])
            self.assertEqual((session.path / "source.raw.log").read_bytes(), raw)
            self.assertIn(b"ERROR I2C NACK", (session.path / "reading_001.raw.log").read_bytes())

    def test_truncated_dump_has_partial_and_complete_previous_reading(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "truncated.log"
            source.write_bytes(encoded_dump(DATA) + collector.BEGIN.encode() + b"\n")
            session = collector.Session(root / "dumps", "A", "offline_log")
            with self.assertRaisesRegex(collector.ProtocolError, "Missing END"):
                collector.convert_log(session, source)
            session.finish("truncated")
            self.assertEqual((session.path / "reading_001.bin").read_bytes(), DATA)
            self.assertEqual((session.path / "reading_002.partial").read_bytes(), b"")
            self.assertFalse((session.path / "reading_002.bin").exists())

    def test_sessions_and_output_files_never_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = collector.Session(root, "A", "offline_log")
            second = collector.Session(root, "A", "offline_log")
            self.assertNotEqual(first.path, second.path)
            occupied = first.path / "reading_001.raw.log"
            occupied.write_bytes(b"preserve")
            with self.assertRaises(FileExistsError):
                first.capture()
            self.assertEqual(occupied.read_bytes(), b"preserve")
            manifest = first.finish("test")
            original = manifest.read_bytes()
            with self.assertRaises(FileExistsError):
                first.finish("attempt to replace")
            self.assertEqual(manifest.read_bytes(), original)

    def test_existing_binary_is_preserved_and_failed_capture_remains_partial(self):
        with tempfile.TemporaryDirectory() as temp:
            session = collector.Session(Path(temp), "A", "offline_log")
            binary = session.path / "reading_001.bin"
            binary.write_bytes(b"existing evidence")
            capture = session.capture()
            for line in encoded_dump(DATA).splitlines(keepends=True):
                capture.feed(line)
            with self.assertRaises(FileExistsError):
                capture.finish()
            capture.finish(error="Existing binary")
            self.assertEqual(binary.read_bytes(), b"existing evidence")
            self.assertEqual((session.path / "reading_001.partial").read_bytes(), DATA)
            self.assertEqual(session.manifest["readings"][0]["status"], "error")

    def test_no_dump_is_not_reported_as_success(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "empty.log"
            source.write_bytes(collector.INFO.encode() + b"\n")
            session = collector.Session(root / "dumps", "A", "offline_log")
            with self.assertRaisesRegex(collector.ProtocolError, "No complete"):
                collector.convert_log(session, source)
            self.assertEqual(session.manifest["readings"], [])

    def test_cli_exit_distinguishes_identical_and_divergent_readings(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            other = bytes([DATA[0] ^ 1]) + DATA[1:]
            for name, second, expected in (("same", DATA, 0), ("different", other, 2)):
                with self.subTest(name=name):
                    source = root / (name + ".log")
                    source.write_bytes(encoded_dump(DATA) + encoded_dump(second))
                    output, errors = io.StringIO(), io.StringIO()
                    with redirect_stdout(output), redirect_stderr(errors):
                        result = collector.main(["--from-log", str(source), "--label", "A",
                                                 "--out", str(root / name)])
                    self.assertEqual(result, expected)
                    self.assertEqual("WARNING: Dump bytes differ" in errors.getvalue(), expected == 2)


if __name__ == "__main__":
    unittest.main()

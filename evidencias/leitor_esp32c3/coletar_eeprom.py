#!/usr/bin/env python3
"""Read-only EEPROM dump collector. Offline conversion uses only the stdlib."""

from __future__ import annotations

import argparse
import binascii
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys
import time
import uuid

SIZE = 32768
BAUD = 115200
INFO = "EEPROM_READER_V1 ADDRESS=0x50 SIZE=32768 SDA=4 SCL=5 HZ=100000"
BEGIN = "BEGIN_EEPROM_V1 SIZE=32768"
DATA_RE = re.compile(r"DATA ([0-9A-F]{4}) ([0-9A-F]{32})\Z")
END_RE = re.compile(r"END_EEPROM_V1 SIZE=32768 CRC32=([0-9A-F]{8})\Z")
CONFIG = {"address": "0x50", "size": SIZE, "sda": 4, "scl": 5,
          "i2c_hz": 100000, "serial_baud": BAUD,
          "dtr": False, "rts": False}


class ProtocolError(ValueError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def line_text(raw: bytes) -> str:
    try:
        return raw.decode("ascii").rstrip("\r\n")
    except UnicodeDecodeError as exc:
        raise ProtocolError("Non-ASCII bytes in protocol") from exc


class DumpParser:
    """Validate one complete dump, including sequence, length, and IEEE CRC32."""

    def __init__(self) -> None:
        self.state = "before_begin"
        self.data = bytearray()
        self.crc32 = None

    def feed(self, raw: bytes) -> bool:
        if self.state == "done":
            raise ProtocolError("Unexpected data after END")
        line = line_text(raw)
        if line.startswith("ERROR "):
            raise ProtocolError("Reader reported: " + line)
        if self.state == "before_begin":
            if line == "" or line == INFO:
                return False
            if line != BEGIN:
                raise ProtocolError("Expected BEGIN_EEPROM_V1 SIZE=32768")
            self.state = "data"
            return False
        match = DATA_RE.fullmatch(line)
        if match:
            address = int(match[1], 16)
            if address != len(self.data) or len(self.data) >= SIZE:
                raise ProtocolError(
                    f"Address sequence error: expected {len(self.data):04X}, got {address:04X}")
            self.data.extend(bytes.fromhex(match[2]))
            return False
        match = END_RE.fullmatch(line)
        if match:
            if len(self.data) != SIZE:
                raise ProtocolError(f"Incomplete dump: {len(self.data)} of {SIZE} bytes")
            computed = binascii.crc32(self.data) & 0xFFFFFFFF
            declared = int(match[1], 16)
            if computed != declared:
                raise ProtocolError(
                    f"CRC32 mismatch: declared {declared:08X}, computed {computed:08X}")
            self.crc32 = f"{computed:08X}"
            self.state = "done"
            return True
        raise ProtocolError(f"Malformed or unexpected line at address {len(self.data):04X}")

    def finish(self) -> bytes:
        if self.state != "done":
            raise ProtocolError(f"Missing END or incomplete dump: {len(self.data)} of {SIZE} bytes")
        return bytes(self.data)


class Session:
    def __init__(self, out: Path, label: str, method: str, reads_requested=None) -> None:
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", label):
            raise ValueError("Label must contain 1-64 ASCII letters, digits, dot, dash or underscore")
        out = out.expanduser().resolve()
        out.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        self.path = out / f"{stamp}_{label}_{uuid.uuid4().hex[:12]}"
        self.path.mkdir()  # No exist_ok: an existing session is never reused.
        self.manifest = {
            "format": "EEPROM_CAPTURE_V1", "created_utc": utc_now(),
            "label": label, "method": method, "config": dict(CONFIG),
            "reads_requested": reads_requested, "readings": [], "events": []}

    def capture(self):
        return Capture(self, len(self.manifest["readings"]) + 1)

    def finish(self, error: str | None = None) -> Path:
        readings = self.manifest["readings"]
        valid = [r for r in readings if r["status"] == "valid"]
        pairs = [{"a": a["index"], "b": b["index"],
                  "identical": a["sha256"] == b["sha256"]}
                 for i, a in enumerate(valid) for b in valid[i + 1:]]
        all_identical = all(p["identical"] for p in pairs) if pairs else None
        comparison_status = ("divergent" if all_identical is False else
                             "identical" if all_identical is True else "not_repeated")
        self.manifest.update({
            "completed_utc": utc_now(),
            "status": "error" if error else "comparison_mismatch" if all_identical is False else "complete",
            "error": error, "valid_readings": len(valid),
            "comparison": {"status": comparison_status, "pairs": pairs,
                           "all_identical": all_identical}})
        target = self.path / "manifest.json"
        with target.open("x", encoding="ascii", newline="\n") as stream:
            json.dump(self.manifest, stream, indent=2, ensure_ascii=True)
            stream.write("\n")
        return target


class Capture:
    def __init__(self, session: Session, index: int) -> None:
        self.session = session
        self.index = index
        self.parser = DumpParser()
        self.started = utc_now()
        self.stem = f"reading_{index:03d}"
        self.raw_path = session.path / (self.stem + ".raw.log")
        self.raw = self.raw_path.open("xb")
        self.closed = False

    def feed(self, raw: bytes) -> bool:
        self.write_raw(raw)
        return self.parser.feed(raw)

    def write_raw(self, raw: bytes) -> None:
        self.raw.write(raw)
        self.raw.flush()

    def finish(self, error: str | None = None) -> None:
        if self.closed:
            raise RuntimeError("Capture already finalized")
        data = bytes(self.parser.data)
        if error is None:
            data = self.parser.finish()
        self.raw.close()
        suffix = ".partial" if error else ".bin"
        binary_path = self.session.path / (self.stem + suffix)
        with binary_path.open("xb") as stream:
            stream.write(data)
        self.session.manifest["readings"].append({
            "index": self.index, "started_utc": self.started,
            "completed_utc": utc_now(), "status": "error" if error else "valid",
            "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            "crc32": self.parser.crc32, "file": binary_path.name,
            "raw_log": self.raw_path.name,
            "raw_sha256": hashlib.sha256(self.raw_path.read_bytes()).hexdigest(),
            "error": error})
        self.closed = True


def convert_log(session: Session, source: Path) -> None:
    """Convert all complete dump blocks. Preserve source and any failing block."""
    source = source.expanduser().resolve()
    session.manifest["source"] = str(source)
    current = None
    prelude = []
    with source.open("rb") as original, (session.path / "source.raw.log").open("xb") as saved:
        try:
            for raw in original:
                saved.write(raw)
                saved.flush()
                if current is None:
                    if line_text(raw) in ("", INFO):
                        prelude.append(raw)
                        continue
                    current = session.capture()
                    for before in prelude:
                        current.feed(before)
                    prelude.clear()
                if current.feed(raw):
                    current.finish()
                    current = None
            if current is not None:
                current.parser.finish()  # Raises on a truncated final block.
            if not session.manifest["readings"]:
                raise ProtocolError("No complete EEPROM dump found in log")
        except BaseException as exc:
            # Keep the rest of the original too, even when validation stops early.
            saved.write(original.read())
            if current is not None and not current.closed:
                current.finish(error=str(exc) or type(exc).__name__)
            raise


def read_serial_line(port, sink, deadline: float) -> bytes:
    pending = bytearray()
    while time.monotonic() < deadline:
        chunk = port.read_until(b"\n", size=256)
        if chunk:
            sink(chunk)
            pending.extend(chunk)
            if len(pending) > 512:
                raise ProtocolError("Serial protocol line exceeds 512 bytes")
            if pending.endswith(b"\n"):
                return bytes(pending)
    raise TimeoutError("Timeout waiting for a complete serial protocol line")


def open_and_identify(session: Session, port_name: str):
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError("Serial mode requires pyserial; offline --from-log uses only stdlib") from exc
    deadline = time.monotonic() + 15.0
    port = None
    last_error = "No INFO response"
    session.manifest["port"] = port_name
    with (session.path / "handshake.raw.log").open("xb") as log:
        while time.monotonic() < deadline:
            try:
                if port is None:
                    port = serial.Serial(port=None, baudrate=BAUD, timeout=0.25, write_timeout=2)
                    port.dtr = False
                    port.rts = False
                    port.port = port_name
                    port.open()
                port.write(b"INFO\n")
                port.flush()
                response_deadline = min(deadline, time.monotonic() + 1.0)
                while time.monotonic() < response_deadline:
                    raw = read_serial_line(port, log.write, response_deadline)
                    line = line_text(raw)
                    if line.startswith("ERROR "):
                        raise ProtocolError("Reader reported: " + line)
                    if line == INFO:
                        session.manifest["info_response"] = line
                        return port
                    if line.startswith("EEPROM_READER_V1"):
                        raise ProtocolError("INFO configuration differs from the required reader configuration")
            except TimeoutError as exc:
                last_error = str(exc)
            except serial.SerialException as exc:
                last_error = str(exc)
                session.manifest["events"].append({"utc": utc_now(), "phase": "handshake", "error": last_error})
                if port is not None:
                    port.close()
                port = None
                time.sleep(min(0.2, max(0, deadline - time.monotonic())))
            except BaseException:
                if port is not None:
                    port.close()
                raise
        if port is not None:
            port.close()
    raise TimeoutError(f"INFO handshake failed within 15 seconds on {port_name}: {last_error}; check port and USB enumeration")


def collect_serial(session: Session, port_name: str, reads: int) -> None:
    port = open_and_identify(session, port_name)
    try:
        for _ in range(reads):
            capture = session.capture()
            try:
                if port.write(b"DUMP\n") != 5:
                    raise IOError("Incomplete DUMP command write; collection aborted without retry")
                port.flush()
                deadline = time.monotonic() + 90.0
                while capture.parser.state != "done":
                    raw = read_serial_line(port, capture.write_raw,
                                           min(deadline, time.monotonic() + 5.0))
                    capture.parser.feed(raw)
                    if time.monotonic() >= deadline and capture.parser.state != "done":
                        raise TimeoutError("DUMP exceeded 90 seconds; collection aborted without retry")
                capture.finish()
            except BaseException as exc:
                if not capture.closed:
                    capture.finish(error=str(exc) or type(exc).__name__)
                raise
    finally:
        port.close()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--port", help="Serial device, for example COM7")
    mode.add_argument("--from-log", type=Path, help="Convert all dump blocks in an Arduino serial log")
    parser.add_argument("--label", required=True, help="EEPROM identification, for example A or B")
    parser.add_argument("--out", type=Path, default=Path(__file__).resolve().parent / "dumps")
    parser.add_argument("--reads", type=int, default=3, help="Serial dump count (default: 3); offline mode converts all blocks")
    args = parser.parse_args(argv)
    if args.reads < 1:
        parser.error("--reads must be at least 1")
    session = None
    error = None
    try:
        session = Session(args.out, args.label,
                          "offline_log" if args.from_log else "serial_read_only",
                          None if args.from_log else args.reads)
        if args.from_log:
            convert_log(session, args.from_log)
        else:
            collect_serial(session, args.port, args.reads)
    except (Exception, KeyboardInterrupt) as exc:
        error = str(exc) or type(exc).__name__
    finally:
        if session is not None:
            manifest = session.finish(error)
            print(f"Session: {session.path}")
            print(f"Manifest: {manifest}")
    if error:
        print("ERROR: " + error, file=sys.stderr)
        return 1
    comparison = session.manifest["comparison"]["all_identical"]
    count = session.manifest["valid_readings"]
    print(f"Validated dumps: {count}; repeated readings identical: {comparison}")
    if comparison is False:
        print("WARNING: Dump bytes differ between readings; transport CRC passed but memory stability is not established.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

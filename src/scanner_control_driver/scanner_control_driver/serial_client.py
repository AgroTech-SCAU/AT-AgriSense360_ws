"""Non-blocking pyserial wrapper for the TimeSyncV2 USB CDC port."""

from __future__ import annotations

import time
from typing import List, Optional

import serial


class SerialClient:
    """Small non-blocking line-oriented serial client.

    The board protocol is strictly request/response, so callers send one line
    and wait for the matching reply.  This class only handles framing; the
    polling state machine lives in :mod:`scanner_control_driver.node`.
    """

    MAX_BUFFER_BYTES = 64 * 1024

    def __init__(
        self,
        port: str,
        baudrate: int = 115200,
        open_settle_s: float = 1.0,
    ) -> None:
        self._port = port
        self._baudrate = baudrate
        self._open_settle_s = open_settle_s
        self._serial: Optional[serial.Serial] = None
        self._buffer = b""
        self._settle_until = 0.0
        self._last_error = ""

    @property
    def is_open(self) -> bool:
        return self._serial is not None and self._serial.is_open

    @property
    def last_error(self) -> str:
        return self._last_error

    @property
    def settle_remaining(self) -> float:
        return max(0.0, self._settle_until - time.monotonic())

    def open(self) -> bool:
        """Open the port.  Returns False and records the error on failure."""
        self.close()
        try:
            self._serial = serial.Serial(
                port=self._port,
                baudrate=self._baudrate,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0,
                write_timeout=1.0,
                rtscts=False,
                dsrdtr=False,
                # The board protocol is request/response.  Refuse a second
                # opener (web console or another node) instead of competing
                # for the same reply bytes.
                exclusive=True,
            )
            self._serial.reset_input_buffer()
            self._buffer = b""
            self._settle_until = time.monotonic() + self._open_settle_s
            self._last_error = ""
            return True
        except (serial.SerialException, OSError) as exc:
            self._serial = None
            self._last_error = str(exc)
            return False

    def close(self) -> None:
        if self._serial is not None:
            try:
                self._serial.close()
            except (serial.SerialException, OSError):
                pass
        self._serial = None
        self._buffer = b""

    def send_line(self, line: str) -> bool:
        """Write one ASCII command with CRLF.  False while settling/failing."""
        if not self.is_open or self.settle_remaining > 0.0:
            return False
        assert self._serial is not None
        try:
            self._serial.write((line + "\r\n").encode("ascii"))
            return True
        except (serial.SerialException, OSError) as exc:
            self._last_error = str(exc)
            self.close()
            return False

    def read_lines(self) -> List[str]:
        """Return all complete lines available without blocking."""
        if not self.is_open:
            return []
        assert self._serial is not None
        try:
            waiting = self._serial.in_waiting
            if waiting:
                self._buffer += self._serial.read(waiting)
        except (serial.SerialException, OSError) as exc:
            self._last_error = str(exc)
            self.close()
            return []

        lines: List[str] = []
        while b"\n" in self._buffer:
            raw, self._buffer = self._buffer.split(b"\n", 1)
            text = raw.rstrip(b"\r").decode("utf-8", "replace").strip()
            if text:
                lines.append(text)

        if len(self._buffer) > self.MAX_BUFFER_BYTES:
            # A stream without newlines is not a valid board reply.  Drop it
            # rather than growing without bound.
            self._buffer = b""
        return lines

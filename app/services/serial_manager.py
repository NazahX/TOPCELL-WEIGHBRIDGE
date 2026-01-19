import random
import re
import threading
import time
from datetime import datetime
from typing import Optional

import serial

from app.config import get_settings
from app.schemas import SerialSettingsPayload, WeightReading


class SerialManager:
    """
    Manages serial (COM/RS232/USB-Serial) communication to read live weights.
    A lightweight background thread keeps the latest reading cached for the API/UI.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self._config = SerialSettingsPayload(simulate=self.settings.allow_weight_simulation)
        self._serial: Optional[serial.Serial] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()
        self._last_weight: Optional[float] = None
        self._last_weight_time: Optional[datetime] = None
        self._connected: bool = False
        self._source: str = "idle"

    def configure(self, payload: SerialSettingsPayload) -> None:
        with self._lock:
            self._config = payload

    def connect(self) -> None:
        self.disconnect()
        config = self._config
        self._stop_event.clear()

        if config.simulate:
            self._connected = False
            self._source = "simulated"
            self._thread = threading.Thread(target=self._simulate_loop, daemon=True)
            self._thread.start()
            return

        if not config.port:
            raise ValueError("Serial port is required to connect")

        try:
            self._serial = serial.Serial(
                port=config.port,
                baudrate=config.baudrate,
                bytesize=config.bytesize,
                parity=config.parity,
                stopbits=config.stopbits,
                timeout=self.settings.serial_read_timeout,
            )
            self._connected = True
            self._source = "serial"
            self._thread = threading.Thread(target=self._reader_loop, daemon=True)
            self._thread.start()
        except Exception as exc:  # serial may throw a variety of errors
            self._connected = False
            self._serial = None
            raise exc

    def disconnect(self) -> None:
        self._stop_event.set()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=0.5)
        if self._serial and self._serial.is_open:
            self._serial.close()
        self._serial = None
        self._connected = False
        self._thread = None
        self._source = "idle"

    def get_reading(self) -> WeightReading:
        with self._lock:
            return WeightReading(
                weight_kg=self._last_weight,
                captured_at=self._last_weight_time,
                connected=self._connected,
                source=self._source,
            )

    def _reader_loop(self) -> None:
        while not self._stop_event.is_set():
            if not self._serial or not self._serial.is_open:
                break
            try:
                raw = self._serial.readline()
                if not raw:
                    continue
                decoded = raw.decode(errors="ignore")
                weight = self._extract_weight(decoded)
                if weight is not None:
                    with self._lock:
                        self._last_weight = weight
                        self._last_weight_time = datetime.utcnow()
            except Exception:
                time.sleep(0.2)

    def _simulate_loop(self) -> None:
        """Produce a slow, random walk weight reading to keep UI/dev flow usable offline."""
        weight = self._last_weight or random.uniform(1200, 1500)
        while not self._stop_event.is_set():
            delta = random.uniform(-2, 2)
            weight = max(0, weight + delta)
            with self._lock:
                self._last_weight = round(weight, 2)
                self._last_weight_time = datetime.utcnow()
            time.sleep(0.5)

    @staticmethod
    def _extract_weight(payload: str) -> Optional[float]:
        # Find the first group of digits (with optional decimal) in the line.
        match = re.search(r"(-?\d+(?:\.\d+)?)", payload)
        if match:
            try:
                return float(match.group(1))
            except ValueError:
                return None
        return None


serial_manager = SerialManager()

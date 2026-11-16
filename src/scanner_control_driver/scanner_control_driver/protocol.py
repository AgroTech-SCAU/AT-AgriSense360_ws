"""Pure parsing and mapping for the TimeSyncV2 USB CDC text protocol.

The board speaks ASCII ``key=value`` lines at 115200 8N1.  This module has no
ROS or serial dependencies so the parsing and message mapping can be tested
without hardware.

One important rule: the board's counters are cumulative for the current power
cycle.  They are useful for pairing triggers with frames inside a recording,
but they are not persistent device identifiers.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

# Mirrors agrisense360_interfaces/msg/TimeSyncStatus.msg so tests do not need
# to import the generated ROS message.
TIME_SOURCE_GNSS_LOCKED = 0
TIME_SOURCE_HOLDOVER = 1
TIME_SOURCE_LOCAL_SYNC = 2
TIME_SOURCE_FAULT = 3

UTC_STATUS_VALID = 0
UTC_STATUS_ESTIMATED = 1
UTC_STATUS_INVALID = 2

_LOCAL_STATES = {"FREE_RUN", "ACQUIRE", "LOCKING"}
_HOLDOVER_STATES = {"HOLDOVER", "REACQUIRE"}
_FAULT_STATES = {"CONFLICT", "FAULT"}


@dataclass(frozen=True)
class KeyValueReply:
    """One parsed reply line."""

    command: str
    values: Dict[str, str]
    raw: str


@dataclass
class BoardSnapshot:
    """Replies collected during one polling cycle."""

    time: Optional[KeyValueReply] = None
    io: Optional[KeyValueReply] = None
    camera: Optional[KeyValueReply] = None
    radar: Optional[KeyValueReply] = None
    link: Optional[KeyValueReply] = None

    def store(self, reply: KeyValueReply) -> bool:
        """Store a reply by command name.  Returns False for unknown commands."""
        attr = {
            "TIME": "time",
            "IO": "io",
            "CAMERA": "camera",
            "RADAR": "radar",
            "LINK": "link",
        }.get(reply.command)
        if attr is None:
            return False
        setattr(self, attr, reply)
        return True


@dataclass(frozen=True)
class StatusFields:
    """Values ready to copy into agrisense360_interfaces/TimeSyncStatus."""

    time_source: int
    utc_status: int
    pps_locked: bool
    gnss_rmc_valid: bool
    lidar_sync_reported: bool
    holdover_seconds: int
    estimated_clock_error_ns: int
    frequency_correction_ppm: float
    pps_count: int
    trigger_count: int
    exposure_feedback_count: int
    camera_clock_mapping_valid: bool
    camera_clock_offset_ns: int
    camera_clock_drift_ppm: float
    detail: str


def parse_reply(line: str) -> Optional[KeyValueReply]:
    """Parse ``COMMAND key=value ...`` into a structured reply.

    Malformed or empty lines return None.  Tokens without ``=`` are ignored;
    this keeps the parser tolerant of the HELP line and future additions.
    """
    text = line.strip()
    if not text:
        return None

    parts = text.split()
    command = parts[0].rstrip(":").upper()
    if not command:
        return None

    values: Dict[str, str] = {}
    for token in parts[1:]:
        if "=" not in token:
            continue
        key, value = token.split("=", 1)
        if key:
            values[key] = value
    return KeyValueReply(command=command, values=values, raw=text)


def _as_int(values: Dict[str, str], key: str, default: int = 0) -> int:
    raw = values.get(key)
    if raw is None:
        return default
    try:
        return int(raw, 0)
    except ValueError:
        return default


def _as_float(values: Dict[str, str], key: str, default: float = 0.0) -> float:
    raw = values.get(key)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _as_csv_ints(values: Dict[str, str], key: str) -> List[int]:
    raw = values.get(key, "")
    result: List[int] = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        try:
            result.append(int(item, 0))
        except ValueError:
            result.append(0)
    return result


def _as_hex_uint64(values: Dict[str, str], key: str) -> int:
    raw = values.get(key)
    if raw is None:
        return 0
    try:
        return int(raw, 16) if raw.lower().startswith("0x") else int(raw, 10)
    except ValueError:
        return 0


def _state(snapshot: BoardSnapshot) -> str:
    if snapshot.time is None:
        return ""
    return snapshot.time.values.get("state", "").upper()


def _mode(snapshot: BoardSnapshot) -> str:
    if snapshot.time is None:
        return ""
    return snapshot.time.values.get("mode", "").upper()


def map_time_source(snapshot: BoardSnapshot) -> int:
    """Map board state to TimeSyncStatus.time_source.

    FREE_RUN/ACQUIRE/LOCKING in GNSS mode are not yet locked, so they are
    reported as LOCAL_SYNC until a real lock exists.  This prevents the
    misleading "GNSS_LOCKED" label before UTC is actually valid.
    """
    if snapshot.time is None:
        # Without a TIME reply the source is unknown; do not claim LOCAL_SYNC.
        return TIME_SOURCE_FAULT

    state = _state(snapshot)
    mode = _mode(snapshot)

    if state in _FAULT_STATES:
        return TIME_SOURCE_FAULT
    if state == "LOCKED" and mode == "GNSS":
        return TIME_SOURCE_GNSS_LOCKED
    if state in _HOLDOVER_STATES:
        return TIME_SOURCE_HOLDOVER
    return TIME_SOURCE_LOCAL_SYNC


def map_utc_status(snapshot: BoardSnapshot) -> int:
    state = _state(snapshot)
    if snapshot.time is None:
        return UTC_STATUS_INVALID
    if state == "LOCKED" and _as_int(snapshot.time.values, "utc_valid") == 1:
        return UTC_STATUS_VALID
    if state in _HOLDOVER_STATES:
        return UTC_STATUS_ESTIMATED
    return UTC_STATUS_INVALID


def _trigger_count(snapshot: BoardSnapshot) -> int:
    if snapshot.camera is None:
        return 0
    pulses = _as_csv_ints(snapshot.camera.values, "pulses")
    # CAM1 is the only channel wired to the MF287 four-camera module.
    return pulses[0] if pulses else 0


def _pps_count(snapshot: BoardSnapshot) -> int:
    if snapshot.time is not None:
        return _as_hex_uint64(snapshot.time.values, "pps64")
    return 0


def _lidar_sync_reported(snapshot: BoardSnapshot) -> bool:
    if snapshot.radar is None:
        return False
    return _as_int(snapshot.radar.values, "active") == 1


def _detail(snapshot: BoardSnapshot, timeouts: int) -> str:
    parts: List[str] = []

    if snapshot.time is None:
        parts.append("time=missing")
    else:
        tv = snapshot.time.values
        parts.extend([
            "state=" + tv.get("state", "?"),
            "mode=" + tv.get("mode", "?"),
            "utc_valid=" + tv.get("utc_valid", "?"),
            "rmc_valid=" + tv.get("rmc_valid", "?"),
            "holdover_flag=" + tv.get("holdover", "?"),
            "freq_ppb=" + tv.get("freq_ppb", "?"),
            "utc_now=" + tv.get("utc_now", "?"),
            "time_now=" + tv.get("time_now", "?"),
            "firmware=" + tv.get("firmware", "?"),
        ])

    if snapshot.io is not None:
        iv = snapshot.io.values
        parts.extend([
            "force1v8=" + iv.get("force1v8", "?"),
            "force3v3=" + iv.get("force3v3", "?"),
            "enabled=" + iv.get("enabled", "?"),
        ])

    if snapshot.camera is not None:
        cv = snapshot.camera.values
        parts.extend([
            "camera_enabled=" + cv.get("enabled", "?"),
            "camera_requested=" + cv.get("requested_enabled", "?"),
            "pulses=" + cv.get("pulses", "?"),
        ])

    if snapshot.radar is not None:
        rv = snapshot.radar.values
        parts.extend([
            "radar_profile=" + rv.get("profile", "?"),
            "radar_active=" + rv.get("active", "?"),
            "radar_pps=" + rv.get("pps_count", "?"),
            "rmc_count=" + rv.get("rmc_count", "?"),
        ])

    if snapshot.link is not None:
        lv = snapshot.link.values
        parts.extend([
            "link_mode=" + lv.get("mode", "?"),
            "link_active=" + lv.get("active", "?"),
        ])

    if timeouts:
        parts.append(f"timeouts={timeouts}")
    return " ".join(parts)


def build_status_fields(
    snapshot: BoardSnapshot,
    timeouts: int = 0,
) -> StatusFields:
    """Build TimeSyncStatus fields from one polling cycle."""
    time_values = snapshot.time.values if snapshot.time is not None else {}
    return StatusFields(
        time_source=map_time_source(snapshot),
        utc_status=map_utc_status(snapshot),
        pps_locked=_state(snapshot) == "LOCKED",
        gnss_rmc_valid=_as_int(time_values, "rmc_valid") == 1,
        lidar_sync_reported=_lidar_sync_reported(snapshot),
        # The board reports holdover as a flag, not seconds.  Keep the numeric
        # field at zero and expose the raw flag in detail.
        holdover_seconds=0,
        estimated_clock_error_ns=0,
        frequency_correction_ppm=_as_float(time_values, "freq_ppb") / 1000.0,
        pps_count=_pps_count(snapshot),
        trigger_count=_trigger_count(snapshot),
        exposure_feedback_count=0,
        camera_clock_mapping_valid=False,
        camera_clock_offset_ns=0,
        camera_clock_drift_ppm=0.0,
        detail=_detail(snapshot, timeouts),
    )

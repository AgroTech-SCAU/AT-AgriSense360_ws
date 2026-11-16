"""ROS 2 adapter for the TimeSyncV2 scanner mainboard.

The node is deliberately read-only: it polls the board's documented query
commands and publishes the resulting state.  It never sends CAMCFG, CAMENABLE,
RADARARM, TIMEMODE or any other command that would change the scanner's
hardware behaviour.  Configuration remains an explicit operator action through
the vendor console or a dedicated future service.
"""

from __future__ import annotations

from collections import deque
import time
from typing import Deque, Optional

import rclpy
from rclpy.node import Node

from agrisense360_interfaces.msg import TimeSyncStatus

from .protocol import BoardSnapshot, build_status_fields, parse_reply
from .serial_client import SerialClient

POLL_COMMANDS = ("TIME", "IO", "CAMERA", "RADAR", "LINK")
STATUS_TOPIC = "/system/time_sync/status"


class ScannerControlDriver(Node):
    """Poll TimeSyncV2 state and publish ``TimeSyncStatus``."""

    def __init__(self) -> None:
        super().__init__("scanner_control_driver")

        self.declare_parameter("port", "/dev/agrisense-timesync")
        self.declare_parameter("baudrate", 115200)
        self.declare_parameter("poll_period_s", 2.0)
        self.declare_parameter("command_timeout_s", 0.4)
        self.declare_parameter("reconnect_period_s", 2.0)
        self.declare_parameter("open_settle_s", 1.0)
        self.declare_parameter("frame_id", "")

        self._port = str(self.get_parameter("port").value)
        self._baudrate = int(self.get_parameter("baudrate").value)
        self._poll_period = float(self.get_parameter("poll_period_s").value)
        self._command_timeout = float(
            self.get_parameter("command_timeout_s").value)
        self._reconnect_period = float(
            self.get_parameter("reconnect_period_s").value)
        self._frame_id = str(self.get_parameter("frame_id").value)

        self._client = SerialClient(
            port=self._port,
            baudrate=self._baudrate,
            open_settle_s=float(self.get_parameter("open_settle_s").value),
        )

        self._publisher = self.create_publisher(
            TimeSyncStatus, STATUS_TOPIC, 10)

        self._queue: Deque[str] = deque()
        self._expected: Optional[str] = None
        self._deadline = 0.0
        self._cycle_active = False
        self._next_poll = 0.0
        self._next_open_attempt = 0.0
        self._snapshot = BoardSnapshot()
        self._timeouts = 0

        self._timer = self.create_timer(0.05, self._tick)
        self.get_logger().info(
            f"waiting for TimeSyncV2 on {self._port} @ {self._baudrate} 8N1")

    def close(self) -> None:
        self._client.close()

    def _tick(self) -> None:
        now = time.monotonic()

        if not self._client.is_open:
            self._try_open(now)
            return

        for line in self._client.read_lines():
            self._handle_line(line, now)

        if self._expected is not None and now >= self._deadline:
            self.get_logger().warn(
                f"timeout waiting for {self._expected} reply")
            self._timeouts += 1
            self._expected = None
            self._send_next(now)

        if not self._cycle_active and now >= self._next_poll:
            self._start_cycle(now)

    def _try_open(self, now: float) -> None:
        if now < self._next_open_attempt:
            return
        self._next_open_attempt = now + self._reconnect_period
        if self._client.open():
            self.get_logger().info(f"opened {self._port}")
            self._next_poll = now + self._client.settle_remaining + 0.2
        else:
            self.get_logger().warn(
                f"cannot open {self._port}: {self._client.last_error}",
                throttle_duration_sec=5.0)

    def _start_cycle(self, now: float) -> None:
        self._snapshot = BoardSnapshot()
        self._timeouts = 0
        self._queue = deque(POLL_COMMANDS)
        self._cycle_active = True
        self._send_next(now)

    def _send_next(self, now: float) -> None:
        if not self._queue:
            self._finish_cycle(now)
            return

        command = self._queue.popleft()
        if not self._client.send_line(command):
            self.get_logger().warn(
                f"write failed on {self._port}: {self._client.last_error}")
            self._client.close()
            self._expected = None
            self._finish_cycle(now)
            return

        self._expected = command
        self._deadline = now + self._command_timeout

    def _handle_line(self, line: str, now: float) -> None:
        reply = parse_reply(line)
        if reply is None:
            return

        if self._expected is not None and reply.command == self._expected:
            self._snapshot.store(reply)
            self._expected = None
            self._send_next(now)
            return

        self.get_logger().debug(f"unexpected board line: {line}")

    def _finish_cycle(self, now: float) -> None:
        self._cycle_active = False
        self._expected = None

        if self._snapshot.time is None and self._snapshot.camera is None:
            self.get_logger().warn(
                "poll cycle produced no usable replies; skipping publish",
                throttle_duration_sec=5.0)
        else:
            self._publish()

        self._next_poll = now + self._poll_period

    def _publish(self) -> None:
        fields = build_status_fields(self._snapshot, self._timeouts)

        msg = TimeSyncStatus()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = self._frame_id
        msg.time_source = fields.time_source
        msg.utc_status = fields.utc_status
        msg.pps_locked = fields.pps_locked
        msg.gnss_rmc_valid = fields.gnss_rmc_valid
        msg.lidar_sync_reported = fields.lidar_sync_reported
        msg.holdover_seconds = fields.holdover_seconds
        msg.estimated_clock_error_ns = fields.estimated_clock_error_ns
        msg.frequency_correction_ppm = fields.frequency_correction_ppm
        msg.pps_count = fields.pps_count
        msg.trigger_count = fields.trigger_count
        msg.exposure_feedback_count = fields.exposure_feedback_count
        msg.camera_clock_mapping_valid = fields.camera_clock_mapping_valid
        msg.camera_clock_offset_ns = fields.camera_clock_offset_ns
        msg.camera_clock_drift_ppm = fields.camera_clock_drift_ppm
        msg.detail = fields.detail
        self._publisher.publish(msg)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = ScannerControlDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == "__main__":
    main()

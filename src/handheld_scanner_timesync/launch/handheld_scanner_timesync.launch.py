"""Launch the read-only TimeSyncV2 mainboard adapter."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config_file = (
        Path(get_package_share_directory("handheld_scanner_timesync"))
        / "config"
        / "handheld_scanner_timesync.yaml"
    )

    port = LaunchConfiguration("port")
    baudrate = LaunchConfiguration("baudrate")
    poll_period = LaunchConfiguration("poll_period_s")

    return LaunchDescription([
        DeclareLaunchArgument(
            "port",
            default_value="/dev/handheld-scanner-timesync",
            description="TimeSyncV2 USB CDC stable device alias.",
        ),
        DeclareLaunchArgument(
            "baudrate",
            default_value="115200",
            description="USB CDC baud rate; the vendor firmware uses 115200 8N1.",
        ),
        DeclareLaunchArgument(
            "poll_period_s",
            default_value="2.0",
            description="Seconds between completed query cycles.",
        ),
        Node(
            package="handheld_scanner_timesync",
            executable="handheld_scanner_timesync",
            name="handheld_scanner_timesync",
            output="screen",
            parameters=[
                str(config_file),
                {
                    "port": port,
                    "baudrate": baudrate,
                    "poll_period_s": poll_period,
                },
            ],
        ),
    ])

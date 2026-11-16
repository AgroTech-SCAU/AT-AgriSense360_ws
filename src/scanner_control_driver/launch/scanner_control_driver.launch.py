"""Launch the read-only TimeSyncV2 scanner mainboard adapter."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description() -> LaunchDescription:
    config_file = (
        Path(get_package_share_directory("scanner_control_driver"))
        / "config"
        / "scanner_control.yaml"
    )

    port = LaunchConfiguration("port")
    baudrate = LaunchConfiguration("baudrate")
    poll_period = LaunchConfiguration("poll_period_s")

    return LaunchDescription([
        DeclareLaunchArgument(
            "port",
            default_value="/dev/agrisense-timesync",
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
            package="scanner_control_driver",
            executable="scanner_control_driver",
            name="scanner_control_driver",
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

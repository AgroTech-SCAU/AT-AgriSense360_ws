"""The only operator-facing launch entry for the integrated scanner."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, LogInfo
from launch.conditions import IfCondition, UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    enable_lidar = LaunchConfiguration("enable_lidar")
    enable_mapping = LaunchConfiguration("enable_mapping")
    enable_control = LaunchConfiguration("enable_control")
    device_config = LaunchConfiguration("device_config")
    control_port = LaunchConfiguration("control_port")

    lidar_launch = Path(
        get_package_share_directory("handheld_scanner_lidar")
    ) / "launch" / "lidar.launch.py"
    mapping_launch = Path(
        get_package_share_directory("handheld_scanner_mapping")
    ) / "launch" / "fast_lio2.launch.py"
    control_launch = Path(
        get_package_share_directory("handheld_scanner_timesync")
    ) / "launch" / "handheld_scanner_timesync.launch.py"

    return LaunchDescription([
        DeclareLaunchArgument(
            "profile",
            default_value="lio",
            description="Device profile. v0.2 defines the lio profile.",
        ),
        DeclareLaunchArgument(
            "enable_lidar",
            default_value="false",
            description="Enable after livox_ros_driver2 and a verified JSON are available.",
        ),
        DeclareLaunchArgument(
            "enable_mapping",
            default_value="false",
            description="Enable only after a FAST-LIO2 ROS 2 implementation is pinned.",
        ),
        DeclareLaunchArgument(
            "device_config",
            default_value="",
            description="Absolute path to the verified device JSON (MID360S for the current lidar).",
        ),
        DeclareLaunchArgument(
            "enable_control",
            default_value="false",
            description="Enable the read-only TimeSyncV2 mainboard adapter.",
        ),
        DeclareLaunchArgument(
            "control_port",
            default_value="/dev/handheld-scanner-timesync",
            description="TimeSyncV2 USB CDC stable device alias.",
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(lidar_launch)),
            launch_arguments={
                "enabled": enable_lidar,
                "device_config": device_config,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(mapping_launch)),
            condition=IfCondition(enable_mapping),
            launch_arguments={"use_sim_time": "false"}.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(control_launch)),
            condition=IfCondition(enable_control),
            launch_arguments={"port": control_port}.items(),
        ),
        LogInfo(
            condition=UnlessCondition(enable_lidar),
            msg="Lidar is disabled; set enable_lidar:=true after installing its pinned driver.",
        ),
    ])

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
    livox_config = LaunchConfiguration("livox_config")

    lidar_launch = Path(
        get_package_share_directory("agrisense360_lidar")
    ) / "launch" / "mid360s.launch.py"
    mapping_launch = Path(
        get_package_share_directory("agrisense360_mapping")
    ) / "launch" / "fast_lio2.launch.py"

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
            "livox_config",
            default_value="",
            description="Absolute path to the verified MID360S driver JSON.",
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(lidar_launch)),
            launch_arguments={
                "enabled": enable_lidar,
                "config_file": livox_config,
            }.items(),
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(str(mapping_launch)),
            condition=IfCondition(enable_mapping),
            launch_arguments={"use_sim_time": "false"}.items(),
        ),
        LogInfo(
            condition=UnlessCondition(enable_lidar),
            msg="MID360S is disabled; set enable_lidar:=true after installing its pinned driver.",
        ),
    ])

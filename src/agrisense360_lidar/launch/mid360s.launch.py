"""AgriSense-360 boundary around the upstream Livox ROS 2 driver."""

import os
from pathlib import Path

from ament_index_python.packages import get_package_prefix
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _local_sdk_environment():
    """Prefer the pinned workspace SDK over another system-wide Livox SDK."""
    package_prefix = Path(get_package_prefix("agrisense360_lidar"))
    for parent in package_prefix.parents:
        sdk_lib = parent / ".deps" / "install" / "livox-sdk2" / "lib"
        if (sdk_lib / "liblivox_lidar_sdk_shared.so").is_file():
            existing = os.environ.get("LD_LIBRARY_PATH", "")
            return {"LD_LIBRARY_PATH": os.pathsep.join(filter(None, (str(sdk_lib), existing)))}
    return {}


def generate_launch_description():
    enabled = LaunchConfiguration("enabled")
    config_file = LaunchConfiguration("config_file")

    return LaunchDescription([
        DeclareLaunchArgument(
            "enabled",
            default_value="false",
            description="Start the MID360S driver after its vendor dependency and JSON are installed.",
        ),
        DeclareLaunchArgument(
            "config_file",
            default_value="",
            description="Absolute path to a verified livox_ros_driver2 MID360S JSON file.",
        ),
        Node(
            condition=IfCondition(enabled),
            package="livox_ros_driver2",
            executable="livox_ros_driver2_node",
            name="mid360s_driver",
            output="screen",
            additional_env=_local_sdk_environment(),
            parameters=[{
                # FAST-LIO2 consumes Livox CustomMsg for the live MID360S path.
                "xfer_format": 1,
                "multi_topic": 0,
                "data_src": 0,
                "publish_freq": 10.0,
                "output_data_type": 0,
                "frame_id": "lidar_link",
                "user_config_path": config_file,
            }],
        ),
    ])

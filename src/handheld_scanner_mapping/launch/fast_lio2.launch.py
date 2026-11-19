"""Handheld-scanner boundary around the pinned ROS 2 FAST-LIO2 candidate."""

from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _validate_extrinsics(context):
    """Reject profiles whose extrinsics would be read out of bounds by FAST-LIO2."""
    config_path = Path(LaunchConfiguration("config_file").perform(context))
    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    params = data.get("/**", {}).get("ros__parameters", {})
    mapping = params.get("mapping", {})
    extrinsic_t = mapping.get("extrinsic_T") or []
    extrinsic_r = mapping.get("extrinsic_R") or []
    if len(extrinsic_t) != 3 or len(extrinsic_r) != 9:
        raise RuntimeError(
            f"{config_path} must define mapping.extrinsic_T (3 values) and "
            "mapping.extrinsic_R (9 values); FAST-LIO2 reads them without "
            "bounds checks"
        )
    return []


def generate_launch_description():
    package_share = Path(get_package_share_directory("handheld_scanner_mapping"))
    default_config = package_share / "config" / "public_mid360_pointcloud2.yaml"

    use_sim_time = LaunchConfiguration("use_sim_time")
    config_file = LaunchConfiguration("config_file")
    map_file_path = LaunchConfiguration("map_file_path")

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("config_file", default_value=str(default_config)),
        DeclareLaunchArgument(
            "map_file_path",
            default_value="/tmp/handheld_scanner_map.pcd",
        ),
        OpaqueFunction(function=_validate_extrinsics),
        Node(
            package="fast_lio",
            executable="fastlio_mapping",
            name="fast_lio2",
            output="screen",
            parameters=[
                config_file,
                {
                    "use_sim_time": use_sim_time,
                    "map_file_path": map_file_path,
                },
            ],
            remappings=[
                ("/Odometry", "/localization/lio/odometry"),
                ("/path", "/localization/lio/path"),
                ("/cloud_registered", "/mapping/cloud_registered"),
                ("/cloud_registered_body", "/mapping/cloud_registered_body"),
                ("/cloud_effected", "/mapping/cloud_effected"),
                ("/Laser_map", "/mapping/laser_map"),
                ("/map_save", "/mapping/save"),
            ],
        ),
    ])

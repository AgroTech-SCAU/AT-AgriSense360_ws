"""AgriSense-360 boundary around the pinned ROS 2 FAST-LIO2 candidate."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(get_package_share_directory("agrisense360_mapping"))
    default_config = package_share / "config" / "public_mid360_pointcloud2.yaml"

    use_sim_time = LaunchConfiguration("use_sim_time")
    config_file = LaunchConfiguration("config_file")
    map_file_path = LaunchConfiguration("map_file_path")

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument("config_file", default_value=str(default_config)),
        DeclareLaunchArgument(
            "map_file_path",
            default_value="/tmp/agrisense360_public_mid360_map.pcd",
        ),
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

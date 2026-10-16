"""Run FAST-LIO2 plus the installed 2D OccupancyGrid mapping backend."""

from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    mapping_share = Path(get_package_share_directory("agrisense360_mapping"))

    use_sim_time = LaunchConfiguration("use_sim_time")
    return LaunchDescription(
        [
            DeclareLaunchArgument("use_sim_time", default_value="true"),
            DeclareLaunchArgument(
                "config_file",
                default_value=str(mapping_share / "config" / "mid360_custom.yaml"),
            ),
            DeclareLaunchArgument(
                "map_file_path",
                default_value="/tmp/agrisense360_offline_map.pcd",
            ),
            DeclareLaunchArgument(
                "cloud_topic", default_value="/mapping/cloud_registered_body"
            ),
            DeclareLaunchArgument("scan_topic", default_value="/mapping/scan"),
            DeclareLaunchArgument(
                "pointcloud_to_scan_params",
                default_value=str(
                    mapping_share / "config" / "offline_pointcloud_to_scan.yaml"
                ),
            ),
            DeclareLaunchArgument(
                "slam_params",
                default_value=str(
                    mapping_share / "config" / "offline_slam_toolbox.yaml"
                ),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(
                    str(mapping_share / "launch" / "fast_lio2.launch.py")
                ),
                launch_arguments={
                    "use_sim_time": use_sim_time,
                    "config_file": LaunchConfiguration("config_file"),
                    "map_file_path": LaunchConfiguration("map_file_path"),
                }.items(),
            ),
            Node(
                package="pointcloud_to_laserscan",
                executable="pointcloud_to_laserscan_node",
                name="pointcloud_to_laserscan",
                output="screen",
                parameters=[
                    LaunchConfiguration("pointcloud_to_scan_params"),
                    {
                        "use_sim_time": ParameterValue(
                            use_sim_time, value_type=bool
                        )
                    },
                ],
                remappings=[
                    ("cloud_in", LaunchConfiguration("cloud_topic")),
                    ("scan", LaunchConfiguration("scan_topic")),
                ],
            ),
            Node(
                package="slam_toolbox",
                executable="async_slam_toolbox_node",
                name="slam_toolbox",
                output="screen",
                parameters=[
                    LaunchConfiguration("slam_params"),
                    {
                        "use_sim_time": ParameterValue(
                            use_sim_time, value_type=bool
                        )
                    },
                ],
            ),
        ]
    )

"""Model-independent camera entry for Handheld-scanner.

The launch arguments and stable topics are frozen. The current module is
selected by `config/adapter_contract.yaml`, so replacing the camera does not
change this file.
"""

from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    package_share = Path(get_package_share_directory("handheld_scanner_camera"))
    contract = yaml.safe_load(
        (package_share / "config" / "adapter_contract.yaml").read_text(encoding="utf-8")
    )
    adapter = contract["adapter"]
    driver = adapter["driver"]
    outputs = {item["name"]: item for item in contract["required_output"]}

    enabled = LaunchConfiguration("enabled")
    use_sim_time = LaunchConfiguration("use_sim_time")

    driver_params = {"use_sim_time": use_sim_time}
    if adapter.get("image_frame_param"):
        driver_params[adapter["image_frame_param"]] = outputs["images"]["frame_id_template"]
    if adapter.get("imu_frame_param"):
        driver_params[adapter["imu_frame_param"]] = outputs["imu"]["frame_id"]
    topic_params = adapter["topic_params"]
    driver_params[topic_params["images"]] = outputs["images"]["topic_template"]
    driver_params[topic_params["temperatures"]] = outputs["temperatures"]["topic_template"]
    driver_params[topic_params["imu"]] = outputs["imu"]["topic"]
    driver_params[topic_params["publisher_count"]] = adapter["source_camera_count"]

    return LaunchDescription([
        DeclareLaunchArgument(
            "enabled",
            default_value="false",
            description="Start the camera driver after its vendor SDK is installed.",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="True when replaying a bag with --clock.",
        ),
        Node(
            condition=IfCondition(enabled),
            package=driver["package"],
            executable=driver["executable"],
            name=driver["node_name"],
            output="screen",
            parameters=[driver_params],
        ),
    ])

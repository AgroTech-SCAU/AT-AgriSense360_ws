"""Model-independent LiDAR entry for Handheld-scanner.

The file name, launch arguments and output topics are frozen. The current
model is selected by `config/adapter_contract.yaml` (`adapter.params_file`
and the node it names), so replacing the LiDAR does not touch this file.
"""

from pathlib import Path

import yaml
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, OpaqueFunction
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def _validate_device_config(context):
    """Refuse to start a driver that would spin without a device JSON."""
    if LaunchConfiguration("enabled").perform(context).lower() not in ("true", "1"):
        return []
    path = Path(LaunchConfiguration("device_config").perform(context))
    if not path.is_file():
        raise RuntimeError(
            "device_config must point to an existing verified device JSON "
            "when enabled:=true"
        )
    return []


def generate_launch_description():
    package_share = Path(get_package_share_directory("handheld_scanner_lidar"))
    contract = yaml.safe_load(
        (package_share / "config" / "adapter_contract.yaml").read_text(encoding="utf-8")
    )
    adapter = contract["adapter"]
    driver = adapter["driver"]
    outputs = {item["name"]: item for item in contract["required_output"]}
    points = outputs["points"]
    imu = outputs["imu"]
    default_params = package_share / "config" / adapter["params_file"]

    enabled = LaunchConfiguration("enabled")
    params_file = LaunchConfiguration("params_file")
    device_config = LaunchConfiguration("device_config")
    frame_id = LaunchConfiguration("frame_id")
    use_sim_time = LaunchConfiguration("use_sim_time")

    if not adapter.get("frame_param"):
        raise RuntimeError(
            "adapter_contract.yaml must declare frame_param for the point cloud"
        )
    if "imu_frame_param" not in adapter:
        raise RuntimeError(
            "adapter_contract.yaml must declare imu_frame_param "
            "(use null if the driver default already matches)"
        )

    driver_params = {
        adapter["device_config_param"]: device_config,
        adapter["frame_param"]: frame_id,
        "use_sim_time": use_sim_time,
    }
    if adapter["imu_frame_param"]:
        driver_params[adapter["imu_frame_param"]] = imu["frame_id"]
    topic_params = adapter["topic_params"]
    driver_params[topic_params["points"]] = points["topic"]
    driver_params[topic_params["imu"]] = imu["topic"]
    driver_params.update(adapter.get("fixed_params", {}))

    return LaunchDescription([
        DeclareLaunchArgument(
            "enabled",
            default_value="false",
            description="Start the LiDAR driver after its vendor dependency and JSON are installed.",
        ),
        DeclareLaunchArgument(
            "params_file",
            default_value=str(default_params),
            description="Driver parameters for the current LiDAR model.",
        ),
        DeclareLaunchArgument(
            "device_config",
            default_value="",
            description="Absolute path to the verified vendor JSON for this device.",
        ),
        DeclareLaunchArgument(
            "frame_id",
            default_value=points["frame_id"],
            description="Frame published by the driver; frozen in frame_contract.yaml.",
        ),
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="True when replaying a bag with --clock.",
        ),
        OpaqueFunction(function=_validate_device_config),
        Node(
            condition=IfCondition(enabled),
            package=driver["package"],
            executable=driver["executable"],
            name=driver["node_name"],
            output="screen",
            parameters=[params_file, driver_params],
        ),
    ])

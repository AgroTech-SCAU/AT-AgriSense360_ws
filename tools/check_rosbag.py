#!/usr/bin/env python3
"""Detect and validate rosbag2 input for an offline FAST-LIO2 run."""

import argparse
from pathlib import Path
import sys

import yaml


FORMATS = {
    "pointcloud2": {
        "lidar_topic": "/livox/points",
        "lidar_type": "sensor_msgs/msg/PointCloud2",
        "imu_topic": "/livox/imu",
    },
    "livox-custom": {
        "lidar_topic": "/livox/lidar",
        "lidar_type": "livox_ros_driver2/msg/CustomMsg",
        "imu_topic": "/livox/imu",
    },
}


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("bag", type=Path, help="rosbag2 directory or metadata.yaml")
    parser.add_argument(
        "--input-format",
        choices=("auto", *FORMATS),
        default="auto",
        help="LiDAR message format; auto detects the two supported layouts",
    )
    parser.add_argument(
        "--format-only",
        action="store_true",
        help="print only the detected format after validation",
    )
    return parser.parse_args()


def load_topics(metadata_path):
    try:
        data = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
        info = data["rosbag2_bagfile_information"]
    except (OSError, KeyError, TypeError, yaml.YAMLError) as exc:
        raise SystemExit(f"invalid rosbag metadata: {metadata_path}: {exc}") from exc

    topics = {
        item["topic_metadata"]["name"]: item
        for item in info.get("topics_with_message_count", [])
    }
    return info, topics


def detect_format(topics):
    matches = []
    for name, spec in FORMATS.items():
        lidar = topics.get(spec["lidar_topic"])
        if lidar and lidar["topic_metadata"].get("type") == spec["lidar_type"]:
            matches.append(name)

    if len(matches) == 1:
        return matches[0]
    if not matches:
        supported = ", ".join(
            f"{spec['lidar_topic']} ({spec['lidar_type']})"
            for spec in FORMATS.values()
        )
        raise SystemExit(f"no supported LiDAR topic found; expected one of: {supported}")
    raise SystemExit(f"multiple supported LiDAR inputs found: {', '.join(matches)}; select --input-format")


def main():
    args = parse_args()
    metadata_path = args.bag if args.bag.name == "metadata.yaml" else args.bag / "metadata.yaml"
    if not metadata_path.is_file():
        raise SystemExit(f"metadata not found: {metadata_path}")

    info, topics = load_topics(metadata_path)
    input_format = detect_format(topics) if args.input_format == "auto" else args.input_format
    spec = FORMATS[input_format]

    required = {
        spec["lidar_topic"]: spec["lidar_type"],
        spec["imu_topic"]: "sensor_msgs/msg/Imu",
    }
    failed = False
    for name, expected_type in required.items():
        item = topics.get(name)
        if item is None:
            print(f"FAIL missing topic: {name}")
            failed = True
            continue
        actual_type = item["topic_metadata"]["type"]
        count = int(item.get("message_count", 0))
        status = "PASS" if actual_type == expected_type and count > 0 else "FAIL"
        if not args.format_only:
            print(f"{status} {name}: type={actual_type}, messages={count}")
        failed |= status == "FAIL"

    if failed:
        return 1
    if args.format_only:
        print(input_format)
        return 0

    duration_ns = int(info.get("duration", {}).get("nanoseconds", 0))
    print(f"PASS input_format={input_format}")
    print(f"INFO storage={info.get('storage_identifier')}, duration={duration_ns / 1e9:.3f}s")
    print(f"INFO total_messages={info.get('message_count', 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

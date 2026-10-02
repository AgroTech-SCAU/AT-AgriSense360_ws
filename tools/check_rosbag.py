#!/usr/bin/env python3
"""Validate rosbag2 metadata before starting an offline mapping run."""

import argparse
from pathlib import Path
import sys

import yaml


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("bag", type=Path, help="rosbag2 directory or metadata.yaml")
    parser.add_argument("--lidar-topic", default="/livox/points")
    parser.add_argument("--imu-topic", default="/livox/imu")
    return parser.parse_args()


def main():
    args = parse_args()
    metadata_path = args.bag if args.bag.name == "metadata.yaml" else args.bag / "metadata.yaml"
    if not metadata_path.is_file():
        raise SystemExit(f"metadata not found: {metadata_path}")

    data = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    info = data["rosbag2_bagfile_information"]
    topics = {
        item["topic_metadata"]["name"]: item
        for item in info.get("topics_with_message_count", [])
    }

    required = {
        args.lidar_topic: "sensor_msgs/msg/PointCloud2",
        args.imu_topic: "sensor_msgs/msg/Imu",
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
        print(f"{status} {name}: type={actual_type}, messages={count}")
        failed |= status == "FAIL"

    duration_ns = int(info.get("duration", {}).get("nanoseconds", 0))
    print(f"INFO storage={info.get('storage_identifier')}, duration={duration_ns / 1e9:.3f}s")
    print(f"INFO total_messages={info.get('message_count', 0)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${workspace_dir}"

fail() {
  echo "$1" >&2
  echo "Run ./tools/import_dependencies.sh and ./tools/build_workspace.sh first." >&2
  exit 1
}

livox_lib="install/livox_ros_driver2/lib/liblivox_ros_driver2.so"
if [[ ! -f "${livox_lib}" ]]; then
  fail "livox_ros_driver2 is not installed."
fi
if ! strings "${livox_lib}" | grep -F "imu_frame_id" > /dev/null; then
  fail "Installed livox_ros_driver2 lacks the output patch (imu_frame_id)."
fi

camera_bin="install/data_cap/lib/data_cap/capture_image_imu"
if [[ ! -x "${camera_bin}" ]]; then
  fail "data_cap is not installed."
fi
if ! strings "${camera_bin}" | grep -F "image_topic_template" > /dev/null; then
  fail "Installed data_cap lacks the output patch (image_topic_template)."
fi

echo "Adapter prerequisites OK."

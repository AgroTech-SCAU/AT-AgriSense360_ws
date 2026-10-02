#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 2 ]]; then
  echo "Usage: $0 BAG_DIRECTORY [OUTPUT_PCD]" >&2
  exit 2
fi

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bag_dir="$(realpath "$1")"
output_pcd="${2:-${workspace_dir}/output/offline_lio/public_mid360_map.pcd}"
output_pcd="$(realpath -m "${output_pcd}")"

"${workspace_dir}/tools/check_rosbag.py" "${bag_dir}"
mkdir -p "$(dirname "${output_pcd}")" "${workspace_dir}/log/ros2"

export ROS_LOG_DIR="${workspace_dir}/log/ros2"
export LD_LIBRARY_PATH="${workspace_dir}/.deps/install/livox-sdk2/lib:${LD_LIBRARY_PATH:-}"

set +u
source /opt/ros/humble/setup.bash
source "${workspace_dir}/install/setup.bash"
set -u

ros2 launch agrisense360_mapping fast_lio2.launch.py \
  use_sim_time:=true map_file_path:="${output_pcd}" &
mapping_pid=$!

stop_mapping() {
  kill -INT "${mapping_pid}" 2>/dev/null || true
  wait "${mapping_pid}" 2>/dev/null || true
}
trap stop_mapping EXIT INT TERM

sleep 2
ros2 bag play "${bag_dir}" --clock 100
sleep 2
ros2 service call /mapping/save std_srvs/srv/Trigger '{}'
sleep 2

stop_mapping
trap - EXIT INT TERM

if [[ ! -s "${output_pcd}" ]]; then
  echo "Mapping finished but no non-empty PCD was produced." >&2
  exit 1
fi

echo "Offline map saved to ${output_pcd}"

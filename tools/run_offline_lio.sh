#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 || $# -gt 3 ]]; then
  echo "Usage: $0 BAG_DIRECTORY [OUTPUT_PCD] [OUTPUT_2D_PREFIX]" >&2
  exit 2
fi

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
bag_dir="$(realpath "$1")"
bag_name="$(basename "${bag_dir}")"
bag_slug="${bag_name// /_}"
output_pcd="${2:-${workspace_dir}/output/offline_lio/${bag_slug}_map.pcd}"
output_pcd="$(realpath -m "${output_pcd}")"
partial_pcd="${output_pcd}.partial.$$"
output_2d_prefix="${3:-}"
if [[ -n "${output_2d_prefix}" ]]; then
  output_2d_prefix="$(realpath -m "${output_2d_prefix}")"
  enable_2d=true
else
  enable_2d=false
fi

if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "ROS 2 Humble was not found at /opt/ros/humble." >&2
  exit 1
fi
if [[ ! -f "${workspace_dir}/install/setup.bash" ]]; then
  echo "Workspace is not built. Run ./tools/build_workspace.sh first." >&2
  exit 1
fi

input_format="$("${workspace_dir}/tools/check_rosbag.py" "${bag_dir}" --format-only)"
"${workspace_dir}/tools/check_rosbag.py" "${bag_dir}" --input-format "${input_format}"

case "${input_format}" in
  pointcloud2)
    lidar_topic="/livox/points"
    config_file="${workspace_dir}/install/agrisense360_mapping/share/agrisense360_mapping/config/public_mid360_pointcloud2.yaml"
    ;;
  livox-custom)
    lidar_topic="/livox/lidar"
    config_file="${workspace_dir}/install/agrisense360_mapping/share/agrisense360_mapping/config/mid360_custom.yaml"
    ;;
  *)
    echo "Unsupported input format: ${input_format}" >&2
    exit 1
    ;;
esac

mkdir -p "$(dirname "${output_pcd}")" "${workspace_dir}/log/ros2"
if [[ "${enable_2d}" == true ]]; then
  mkdir -p "$(dirname "${output_2d_prefix}")"
fi

# ROS 2 Humble is built against the system toolchain. Do not load Conda's
# incompatible C++ runtime into mapping or rosbag processes.
export PATH="/opt/ros/humble/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PYTHON_EXE PYTHONHOME
export ROS_LOG_DIR="${workspace_dir}/log/ros2"
export LD_LIBRARY_PATH="${workspace_dir}/.deps/install/livox-sdk2/lib:${LD_LIBRARY_PATH:-}"

set +u
source /opt/ros/humble/setup.bash
source "${workspace_dir}/install/setup.bash"
set -u

if [[ "${enable_2d}" == true ]]; then
  mapping_launch="offline_maps.launch.py"
else
  mapping_launch="fast_lio2.launch.py"
fi

ros2 launch agrisense360_mapping "${mapping_launch}" \
  use_sim_time:=true \
  config_file:="${config_file}" \
  map_file_path:="${partial_pcd}" &
mapping_pid=$!

stop_mapping() {
  if ! kill -0 "${mapping_pid}" 2>/dev/null; then
    return
  fi
  kill -TERM "${mapping_pid}" 2>/dev/null || true
  for _ in {1..50}; do
    if ! kill -0 "${mapping_pid}" 2>/dev/null; then
      wait "${mapping_pid}" 2>/dev/null || true
      return
    fi
    sleep 0.1
  done
  kill -KILL "${mapping_pid}" 2>/dev/null || true
  wait "${mapping_pid}" 2>/dev/null || true
}
cleanup() {
  stop_mapping
  rm -f "${partial_pcd}"
}
trap cleanup EXIT INT TERM

service_ready=false
for _ in {1..30}; do
  if ros2 service list | grep -qx "/mapping/save"; then
    service_ready=true
    break
  fi
  sleep 0.5
done
if [[ "${service_ready}" != true ]]; then
  echo "FAST-LIO2 did not expose /mapping/save within 15 seconds." >&2
  exit 1
fi

echo "Replaying ${input_format} data and writing the map to ${output_pcd}"
ros2 bag play "${bag_dir}" --clock 100 --topics "${lidar_topic}" /livox/imu
sleep 2
ros2 service call /mapping/save std_srvs/srv/Trigger '{}'
if [[ "${enable_2d}" == true ]]; then
  ros2 run nav2_map_server map_saver_cli \
    -t /map \
    -f "${output_2d_prefix}" \
    --fmt pgm \
    --ros-args \
      -p map_subscribe_transient_local:=true \
      -p save_map_timeout:=30.0
fi
sleep 2

stop_mapping

if [[ ! -s "${partial_pcd}" ]]; then
  echo "Mapping finished but no non-empty PCD was produced." >&2
  exit 1
fi
mv -f "${partial_pcd}" "${output_pcd}"
if [[ "${enable_2d}" == true ]] && \
   [[ ! -s "${output_2d_prefix}.pgm" || ! -s "${output_2d_prefix}.yaml" ]]; then
  echo "3D mapping succeeded but the 2D OccupancyGrid was not saved." >&2
  exit 1
fi
trap - EXIT INT TERM

echo "Offline map saved to ${output_pcd}"
if [[ "${enable_2d}" == true ]]; then
  echo "2D occupancy map saved to ${output_2d_prefix}.pgm and ${output_2d_prefix}.yaml"
fi

#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${workspace_dir}"

# ROS 2 Humble on Ubuntu 22.04 is built against the system Python 3.10.
# Keep user Conda environments from leaking into rosidl/CMake discovery.
export PATH="/opt/ros/humble/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PYTHON_EXE PYTHONHOME

if [[ ! -f /opt/ros/humble/setup.bash ]]; then
  echo "ROS 2 Humble was not found at /opt/ros/humble." >&2
  exit 1
fi

set +u
source /opt/ros/humble/setup.bash
set -u

livox_sdk_prefix="${workspace_dir}/.deps/install/livox-sdk2"
if [[ -d "${livox_sdk_prefix}" ]]; then
  export CMAKE_PREFIX_PATH="${livox_sdk_prefix}:${CMAKE_PREFIX_PATH:-}"
  export LD_LIBRARY_PATH="${livox_sdk_prefix}/lib:${LD_LIBRARY_PATH:-}"
fi

# The adapter packages set output topics/frames through driver parameters.
# Without the patches the drivers silently keep vendor names, so fail early.
check_vendor_patch() {
  local repo="$1" patch="$2"
  if ! git -C "${repo}" apply --reverse --check "${patch}" 2>/dev/null; then
    echo "Vendor patch not applied: ${patch}" >&2
    echo "Run ./tools/import_dependencies.sh first." >&2
    exit 1
  fi
}
check_vendor_patch "src/vendor/livox_ros_driver2" \
  "patches/livox_ros_driver2/0001-parameterize-outputs.patch"
check_vendor_patch "src/vendor/CyperstereoSDK" \
  "patches/CyperstereoSDK/0001-parameterize-outputs.patch"

# Build only src/.  third_party/ is deliberately outside this colcon
# invocation: Livox-SDK2 is installed into .deps by build_livox_sdk2.sh, and
# Kalibr is ROS 1/catkin and runs in its own container.
#
# The camera SDK also ships ROS 1/catkin packages, standalone CMake tools and
# samples under src/vendor.  Only ros2/src/data_cap belongs to the Humble
# workspace, so use an explicit allow-list instead of scanning every package.
workspace_packages=(
  handheld_scanner_bringup
  handheld_scanner_camera
  handheld_scanner_description
  handheld_scanner_interfaces
  handheld_scanner_lidar
  handheld_scanner_mapping
  handheld_scanner_timesync
  livox_ros_driver2
  fast_lio
  data_cap
)

colcon build \
  --base-paths src \
  --packages-select "${workspace_packages[@]}" \
  --symlink-install \
  --cmake-args \
    --no-warn-unused-cli \
    -DROS_EDITION=ROS2 \
    -DDISTRO_ROS=humble \
    -DPYTHON_EXECUTABLE=/usr/bin/python3 \
    -DPython3_EXECUTABLE=/usr/bin/python3

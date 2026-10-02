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

colcon build \
  --symlink-install \
  --cmake-args \
    --no-warn-unused-cli \
    -DROS_EDITION=ROS2 \
    -DDISTRO_ROS=humble \
    -DPYTHON_EXECUTABLE=/usr/bin/python3 \
    -DPython3_EXECUTABLE=/usr/bin/python3

#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${workspace_dir}"

export PATH="/opt/ros/humble/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
unset CONDA_PREFIX CONDA_DEFAULT_ENV CONDA_PYTHON_EXE PYTHONHOME

vcs import . < dependencies.repos

driver_dir="${workspace_dir}/src/vendor/livox_ros_driver2"
fast_lio_dir="${workspace_dir}/src/vendor/FAST_LIO_ROS2"
fast_lio_patch="${workspace_dir}/patches/fast_lio_ros2/0001-parameterize-output-frames.patch"
camera_dir="${workspace_dir}/src/vendor/CyperstereoSDK"
camera_patch="${workspace_dir}/patches/CyperstereoSDK/0001-parameterize-outputs.patch"

if [[ ! -e "${driver_dir}/package.xml" ]]; then
  ln -s package_ROS2.xml "${driver_dir}/package.xml"
fi

git -C "${fast_lio_dir}" submodule update --init --recursive

if git -C "${fast_lio_dir}" apply --check "${fast_lio_patch}"; then
  git -C "${fast_lio_dir}" apply "${fast_lio_patch}"
elif git -C "${fast_lio_dir}" apply --reverse --check "${fast_lio_patch}"; then
  echo "Handheld-scanner FAST-LIO2 frame patch is already applied."
else
  echo "FAST-LIO2 frame patch does not match the pinned source." >&2
  exit 1
fi

driver_patch="${workspace_dir}/patches/livox_ros_driver2/0001-parameterize-outputs.patch"
if git -C "${driver_dir}" apply --check "${driver_patch}"; then
  git -C "${driver_dir}" apply "${driver_patch}"
elif git -C "${driver_dir}" apply --reverse --check "${driver_patch}"; then
  echo "Handheld-scanner livox IMU-frame patch is already applied."
else
  echo "Livox IMU-frame patch does not match the pinned source." >&2
  exit 1
fi

if git -C "${camera_dir}" apply --check "${camera_patch}"; then
  git -C "${camera_dir}" apply "${camera_patch}"
elif git -C "${camera_dir}" apply --reverse --check "${camera_patch}"; then
  echo "Handheld-scanner camera output-frame patch is already applied."
else
  echo "CyperstereoSDK output-frame patch does not match the pinned source." >&2
  exit 1
fi

vcs status .

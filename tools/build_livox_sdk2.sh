#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source_dir="${workspace_dir}/third_party/sources/Livox-SDK2"
build_dir="${workspace_dir}/.deps/build/livox-sdk2"
install_dir="${workspace_dir}/.deps/install/livox-sdk2"

if [[ ! -f "${source_dir}/CMakeLists.txt" ]]; then
  echo "Livox-SDK2 is missing. Run tools/import_dependencies.sh first." >&2
  exit 1
fi

cmake -S "${source_dir}" -B "${build_dir}" \
  -DCMAKE_BUILD_TYPE=Release \
  -DCMAKE_INSTALL_PREFIX="${install_dir}"
cmake --build "${build_dir}" --parallel
cmake --install "${build_dir}"

echo "Livox-SDK2 installed locally at ${install_dir}"

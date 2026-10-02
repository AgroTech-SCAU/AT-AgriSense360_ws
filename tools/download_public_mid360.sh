#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
dataset_dir="${workspace_dir}/datasets/public/driving_slam_mid360"
archive_name="rosbag2_2024_04_16-14_17_01.zip"
archive_path="${dataset_dir}/${archive_name}"
partial_path="${archive_path}.part"
extract_path="${dataset_dir}/extracted"
source_url="https://zenodo.org/records/14841855/files/${archive_name}?download=1"
expected_size="517088133"
expected_sha256="f8f89eebf2aaf9cc1d465bfa5451bbb599cd92d079b59949104bb4e5cb619bdd"
expected_md5="0836c50859bb1af591966b69da166186"

mkdir -p "${dataset_dir}"

verify_archive() {
  local candidate="$1"
  [[ -f "${candidate}" ]] || return 1
  [[ "$(stat -c '%s' "${candidate}")" == "${expected_size}" ]] || return 1
  [[ "$(sha256sum "${candidate}" | cut -d ' ' -f 1)" == "${expected_sha256}" ]] || return 1
  [[ "$(md5sum "${candidate}" | cut -d ' ' -f 1)" == "${expected_md5}" ]] || return 1
}

if ! verify_archive "${archive_path}"; then
  echo "Downloading the checksum-pinned public MID360 dataset..."
  curl --location --fail --retry 3 --continue-at - \
    --output "${partial_path}" "${source_url}"

  if ! verify_archive "${partial_path}"; then
    echo "Downloaded archive failed size or checksum validation." >&2
    exit 1
  fi
  mv "${partial_path}" "${archive_path}"
fi

if [[ ! -d "${extract_path}" ]]; then
  extract_tmp="$(mktemp -d "${dataset_dir}/.extract.XXXXXX")"
  cleanup_extract_tmp() {
    rm -rf "${extract_tmp}"
  }
  trap cleanup_extract_tmp EXIT
  unzip -q "${archive_path}" -d "${extract_tmp}"
  mv "${extract_tmp}" "${extract_path}"
  trap - EXIT
fi

bag_metadata="$(find "${extract_path}" -name metadata.yaml -type f -print -quit)"
if [[ -z "${bag_metadata}" ]]; then
  echo "No rosbag2 metadata.yaml was found after extraction." >&2
  exit 1
fi

echo "Dataset ready: $(dirname "${bag_metadata}")"

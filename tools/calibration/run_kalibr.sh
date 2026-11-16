#!/usr/bin/env bash
set -euo pipefail

workspace_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
kalibr_src="${workspace_dir}/third_party/sources/kalibr"
dockerfile="${workspace_dir}/tools/calibration/Dockerfile"
image="${KALIBR_IMAGE:-agrisense360/kalibr:1f60227}"

if [[ ! -f "${kalibr_src}/aslam_offline_calibration/kalibr/package.xml" ]]; then
  echo "Kalibr source not found at ${kalibr_src}." >&2
  echo "Fetch the pinned source (GitHub access required) and retry:" >&2
  echo "  ./tools/import_dependencies.sh" >&2
  exit 1
fi

if ! docker image inspect "${image}" >/dev/null 2>&1; then
  echo "Building ${image}; the first build takes roughly 10-20 minutes." >&2
  docker build \
    --build-arg "BUILD_JOBS=${KALIBR_BUILD_JOBS:-4}" \
    -f "${dockerfile}" \
    -t "${image}" \
    "${kalibr_src}"
fi

run_args=(--rm -i)

if [[ -t 0 && -t 1 ]]; then
  run_args+=(-t)
fi

# Run as the host user so calibration outputs under /ws are not root-owned.
run_args+=(
  --user "$(id -u):$(id -g)"
  -e "HOME=/tmp"
  -v "${workspace_dir}:/ws"
  -w /ws
)

# Optional X11 pass-through for kalibr's --show-extraction window.
if [[ -n "${DISPLAY:-}" && -d /tmp/.X11-unix ]]; then
  run_args+=(
    -e "DISPLAY=${DISPLAY}"
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw
  )
  if [[ -f "${HOME}/.Xauthority" ]]; then
    run_args+=(
      -e "XAUTHORITY=/tmp/.Xauthority"
      -v "${HOME}/.Xauthority:/tmp/.Xauthority:ro"
    )
  fi
fi

# Camera capture inside the container (SDK's V4L2 path needs /dev/video*).
if [[ "${KALIBR_CAPTURE:-0}" == "1" ]]; then
  shopt -s nullglob
  video_devices=(/dev/video*)
  shopt -u nullglob
  if [[ "${#video_devices[@]}" -eq 0 ]]; then
    echo "KALIBR_CAPTURE=1 but no /dev/video* devices were found." >&2
    exit 1
  fi
  for dev in "${video_devices[@]}"; do
    run_args+=(--device "${dev}")
  done
  video_gid="$(getent group video | cut -d: -f3)"
  if [[ -n "${video_gid}" ]]; then
    run_args+=(--group-add "${video_gid}")
  fi
fi

exec docker run "${run_args[@]}" "${image}" "$@"

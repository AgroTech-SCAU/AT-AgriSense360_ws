# Kalibr calibration container

Kalibr is ROS 1 only and has no ROS 2 port. The project keeps it in a separate
Noetic container instead of installing ROS 1 on the Humble host, per
`docs/01_project_baseline.md` section 6.

Source: `third_party/sources/kalibr`, pinned by `dependencies.repos` to
`1f60227442d25e36365ef5f72cd80b9666d73467` (upstream `master`).

If that directory was populated from a source tarball instead of `vcs import`,
it is not a git checkout and `vcs import` will refuse to overwrite it. Remove
the directory before re-running `./tools/import_dependencies.sh` on a machine
with GitHub access.

## Build and enter

```bash
./tools/calibration/run_kalibr.sh
```

The first invocation builds the image. Later invocations start it directly.
The workspace is mounted at `/ws`; the container runs as the host UID so files
written under `/ws` stay owned by you.

Run a single command:

```bash
./tools/calibration/run_kalibr.sh \
  rosrun kalibr kalibr_calibrate_cameras --help
```

Build parallelism defaults to 4 because Kalibr's C++ targets are memory
hungry. Override with `KALIBR_BUILD_JOBS=8`.

## Calibration target

The CyperStereo official tutorial uses an AprilGrid named
`april_6x6_80x80cm`. Generate it with Kalibr's own target generator:

```bash
./tools/calibration/run_kalibr.sh \
  rosrun kalibr kalibr_create_target_pdf \
  --type apriltag --nx 6 --ny 6 --tsize 0.088 --tspace 0.3 --tfam t36h11 \
  /ws/config/local/april_6x6_80x80cm.pdf
```

The generator crops tightly to the tags. Add a 3.5 cm white border on the host
without scaling the tags (Ghostscript `PageOffset`), producing an 0.80 x 0.80 m
page:

```bash
gs -q -o config/local/april_6x6_80x80cm-bordered.pdf \
  -sDEVICE=pdfwrite -dFIXEDMEDIA \
  -dDEVICEWIDTHPOINTS=2267.717 -dDEVICEHEIGHTPOINTS=2267.717 \
  -c "<</PageOffset [99.1 99.1]>> setpagedevice" \
  -f config/local/april_6x6_80x80cm.pdf
```

Print at 100% scale on A0 or tile it; never use "fit to page". The generator
draws the black corner squares between tags by design (`symmCorners`) - they
are part of Kalibr's AprilGrid, not a printing defect.

Put the verified target file under `config/local/` (gitignored), for example
`config/local/april_6x6_80x80cm.yaml`:

```yaml
target_type: 'aprilgrid'
tagCols: 6
tagRows: 6
tagSize: 0.088        # measured tag edge length in metres
tagSpacing: 0.3      # spacing / tagSize, measured on the printed board
```

`tagSize` and `tagSpacing` must come from the actual printed target. Do not
copy example values into a production calibration.

## Intrinsics and multi-camera extrinsics

```bash
./tools/calibration/run_kalibr.sh bash
```

Inside the container:

```bash
cd /ws
rosrun kalibr kalibr_calibrate_cameras \
  --bag /ws/datasets/calibration/quad_calibra.bag \
  --topics /cam0/image_raw /cam1/image_raw /cam2/image_raw /cam3/image_raw \
  --models pinhole-equi pinhole-equi pinhole-equi pinhole-equi \
  --target /ws/config/local/april_6x6_80x80cm.yaml
```

`pinhole-equi` is the equidistant fisheye model used by the CyperStereo
factory/SDK calibration files.

Kalibr builds a chain and expects overlapping fields of view between
consecutive cameras. If the 160° and 200° pairs do not overlap as one chain,
calibrate each overlapping pair separately and then combine the rig extrinsics;
do not force four non-overlapping cameras into one run.

## Camera-IMU

```bash
rosrun kalibr kalibr_calibrate_imu_camera \
  --bag /ws/datasets/calibration/quad_calibra.bag \
  --cam /ws/config/local/quad_calibra-camchain.yaml \
  --imu /ws/config/local/bmi088_imu_param.yaml \
  --target /ws/config/local/april_6x6_80x80cm.yaml
```

The IMU noise parameters must come from an Allan-variance run or the IMU
datasheet; they are not committed here.

## Data

Kalibr reads ROS 1 bags. Record with the SDK's ROS 1 capture node, or record a
ROS 2 bag with `data_cap` and convert it to a ROS 1 bag before starting Kalibr.
The topic names above assume `/cam0/image_raw` ... `/cam3/image_raw` and
`/imu0`, which is what `data_cap` publishes.

## Camera access

`KALIBR_CAPTURE=1 ./tools/calibration/run_kalibr.sh` exposes `/dev/video*` and
the host `video` group. The SDK's ROS 1 capture workspace still has to be built
inside the container or run separately; this image contains Kalibr only.

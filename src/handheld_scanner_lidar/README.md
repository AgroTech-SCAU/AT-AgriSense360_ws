# handheld_scanner_lidar

Model-independent boundary between Handheld-scanner and the LiDAR driver.
Every LiDAR model is expected to reach the same stable outputs through this
package, so mapping, bringup and application code never see a vendor topic or
a model-specific message type.

## Current model

| Item | Value |
|---|---|
| Model | Livox MID360S |
| Driver | `livox_ros_driver2` 1.2.6, commit `13eb05e4e6dd7a765b934d0c5fd6236676a57b49` |
| Node | `mid360s_driver` |
| Points output | `/sensors/lidar/points` (`sensor_msgs/PointCloud2`) |
| IMU output | `/sensors/lidar/imu` (`sensor_msgs/Imu`) |
| Status | evaluation pin; calibration `UNCALIBRATED` |

## Stable interface

See `config/adapter_contract.yaml`. The `required_output` section is frozen:

- points are `sensor_msgs/PointCloud2` with fields
  `x, y, z, intensity, tag, line` (Livox `LivoxPointXyzitl` layout) plus an
  extra `timestamp` field, metres; stamps use the device timebase;
- IMU is `sensor_msgs/Imu` in SI units, REP-103 axes, reliable QoS.

Changing a topic, type, field set or frame is an interface change: update
`topic_contract.yaml` first, then this contract, then the consumers.

## Files

| File | Changes with |
|---|---|
| `launch/lidar.launch.py` | never; it reads the model from the contract |
| `config/mid360s.yaml` | current model values |
| `config/adapter_contract.yaml` | `adapter` section per model; `required_output` is frozen |

Per-device data (serial number, IPv4, UDP ports) is never stored here. It is
passed at launch time as `device_config` and lives outside Git.

## Run

```bash
ros2 launch handheld_scanner_lidar lidar.launch.py \
  enabled:=true device_config:=/absolute/path/to/verified_mid360s.json
```

Verify before connecting anything downstream:

```bash
ros2 topic info -v /sensors/lidar/points
ros2 topic hz /sensors/lidar/points
ros2 topic echo --once /sensors/lidar/imu
```

The vendor driver creates publishers lazily on the first data packet, so
`ros2 topic info` reports "Unknown topic" until the LiDAR is streaming.

Run `./tools/check_adapters.sh` after building: it fails if the installed
driver predates the output patch. Keep the workspace in place — the Livox
library records absolute RUNPATHs to `.deps/`, so a copied `install/` will
not load.

## Replacing the LiDAR

1. **Driver** — add the new driver to `dependencies.repos` at an immutable
   commit, check its licence, and keep it out of this package.
2. **Parameters** — add `config/<new_model>.yaml` with only verified values;
   leave unknown fields out or mark them `UNCONFIRMED`.
3. **Adapter** — rewrite the `adapter` section of `adapter_contract.yaml`:
   driver package/executable/node name, parameter file, source topics,
   `device_config_param` and conversion steps. `required_output` must not
   change.
4. **Launch** — no edit. `launch/lidar.launch.py` is model-independent and
   reads every model-specific value from the contract.
5. **Message alignment** — if the model cannot publish the required field set
   natively, add a converter in this package. It must keep the per-point time
   field and the header stamp semantics.
6. **Time and axes** — confirm the host/device timebase, per-point time unit
   and IMU axis order. Do not fill in measured values without a measurement.
7. **Verify** — topic type/hz/echo, a bag replay, then 30 minutes on hardware.
8. **Rollback** — keep the previous model's params file and driver pin so the
   old configuration can be restored without reverting this package.

## Decoupling boundaries

Topics, message types, frames and launch arguments are decoupled from the
vendor. Three couplings remain and must be handled when adapting another
LiDAR:

- **Point layout.** `required_output` still describes the Livox
  `LivoxPointXyzitl` layout (`x, y, z, intensity, tag, line, timestamp`).
  FAST-LIO2's `lidar_type: 4` handler parses exactly that layout, so a
  PointCloud2 with different fields is accepted by type checkers and then
  parsed incorrectly. A non-Livox LiDAR must either publish the same fields
  through a converter in this package, or come with a matching consumer
  handler in mapping.
- **Driver parameters.** `pointcloud_topic`, `imu_topic` and `imu_frame_id`
  exist only through
  `patches/livox_ros_driver2/0001-parameterize-outputs.patch`. A different
  SDK needs an equivalent parameterisation (a new patch) or a relay inside
  this package; do not move vendor names into the contract or edit the
  launch file around it.
- **IMU semantics.** Message type and frame are decoupled, but axes, units
  and the LiDAR-to-IMU transform are not verified. A replacement IMU must be
  validated against the same contract before consumers trust it.

## Not yet verified on hardware

The fields listed under `verification_required` in the adapter contract:
serial number, firmware version, IPv4/UDP ports, rates/QoS, timestamp
semantics and the LiDAR-to-IMU transform. Until they are measured, treat the
live path as unverified; the frame contract stays `UNCALIBRATED`.

Known dependency: the vendor driver initially hardcodes the IMU header frame
to `livox_frame`. This package relies on the project patch
`patches/livox_ros_driver2/0001-parameterize-outputs.patch`, applied by
`tools/import_dependencies.sh`, which adds `imu_frame_id`,
`pointcloud_topic` and `imu_topic`.

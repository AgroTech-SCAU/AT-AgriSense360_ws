# handheld_scanner_camera

Model-independent camera boundary between Handheld-scanner and the camera
vendor SDK. Version 0.1 covers the CyperStereo MF287 through `data_cap`.

## Current model

| Item | Value |
|---|---|
| Model | CyperStereo MF287 |
| Driver | `data_cap` (`capture_image_imu`, node `data_publisher`), CyperstereoSDK commit `30e1a7899f419af08f59cb476ddb87c5514de189` |
| Images | `/sensors/camera/cam0..3/image_raw` (`sensor_msgs/Image`) |
| Temperatures | `/sensors/camera/cam0..3/temperature` (`sensor_msgs/Temperature`) |
| IMU | `/sensors/camera/imu` (`sensor_msgs/Imu`) |
| Status | `INTERFACE_CONFIRMED_DRIVER_PENDING`; calibration `UNCALIBRATED` |

`data_cap` is a vendored package from `CyperstereoSDK` (`ros2/src/data_cap`);
only that package is built by `tools/build_workspace.sh`.

## Stable interface

See `config/adapter_contract.yaml`. The `required_output` section is frozen:

- four images plus four `CameraInfo` topics (the latter required after
  calibration, not yet published);
- four temperature topics, treated as diagnostics;
- one IMU topic in frame `camera_imu_link`.

## Files

| File | Changes with |
|---|---|
| `launch/camera.launch.py` | never; it reads the model from the contract |
| `config/mf287.yaml` | current model facts (record only, see below) |
| `config/adapter_contract.yaml` | `adapter` section per model; `required_output` is frozen |

Apart from the six parameters added by the project patch (two frame ids,
three topic templates and `publisher_count`), `data_cap` declares no ROS
parameters, so `mf287.yaml` is documentation for operators and future
adapters, not driver input. The package exposes only `enabled` and
`use_sim_time`; frames and topics are fixed by the contract and passed to the
driver as parameters. Calibration, when it exists, will be passed to a future
driver as an absolute path outside this package.

## Run

```bash
ros2 launch handheld_scanner_camera camera.launch.py enabled:=true
```

Verify:

```bash
ros2 topic hz /sensors/camera/cam0/image_raw
ros2 topic echo --once /sensors/camera/imu
```

The adapter advertises six image and six temperature topics plus one IMU
topic. On four-camera hardware cam4/cam5 are advertised but silent, so nine
streams carry data: cam0..3 image, cam0..3 temperature and the IMU. The
publishers are created before any frame arrives, so `ros2 topic list` shows
them even without streaming.

Run `./tools/check_adapters.sh` after building: it fails if the installed
`data_cap` predates the output patch. Make sure the driver is not already
running elsewhere — the USB device is exclusive.

## Replacing the camera

1. **Driver** — add the new driver to `dependencies.repos` at an immutable
   commit and check its licence.
2. **Facts** — add `config/<new_model>.yaml` describing the module.
3. **Adapter** — rewrite the `adapter` section: driver package/executable/
   node name, source topic templates, camera count, conversion steps.
   `required_output` must not change.
4. **Launch** — no edit. The file is model-independent.
5. **Message alignment** — if the model cannot publish the required types
   natively, add a converter in this package.
6. **Frames and time** — map header frames to `frame_contract.yaml` and
   confirm the timebase; do not invent transforms.
7. **Verify** — topic list/hz/echo, a bag replay, then hardware.
8. **Rollback** — keep the previous model record and driver pin.

## Visual fusion (v0.5)

`docs/05_development_roadmap.md` P3.4 plans FAST-LIVO2 or an equivalent
LiDAR-inertial-visual pipeline. That consumer needs one image stream plus
`CameraInfo`; which of cam0..3 becomes the visual primary is not decided yet,
and the other streams are not its input. The four-stream contract above stays
in place so the choice can be made without republishing the driver.

## Known gaps

- Frames and topics rely on the project patch
  `patches/CyperstereoSDK/0001-parameterize-outputs.patch`, applied by
  `tools/import_dependencies.sh`. It adds `image_frame_template`,
  `imu_frame_id`, `image_topic_template`, `temperature_topic_template`,
  `imu_topic` and `publisher_count`; without it the driver hardcodes
  `camN` / `imu0` and `/camN/...` topics.
- No `CameraInfo` is published; calibration outputs are not wired yet.
- The adapter asks for six publishers (`publisher_count: 6`). `/cam4` and
  `/cam5` are advertised under the stable names but stay silent in four-camera
  mode. Six-image firmware changes the layout:
  cam2..cam5 become half-width/half-height (640x512) images, outside the
  frozen contract.
- Header stamps come from the camera device timebase, not the mainboard.
  Mainboard triggering and host sync remain unverified (see
  `handheld_scanner_timesync` and `docs/04_integrated_scanner_rnd_baseline.md`
  §4.3).

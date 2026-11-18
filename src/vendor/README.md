# Third-party dependency policy

Do not copy or clone floating branches into this directory.

Each dependency must be reviewed and recorded with:

- upstream URL and immutable commit/tag;
- license and local modifications;
- ROS distribution and message compatibility;
- owner, update method and rollback procedure;
- a bag-replay or hardware smoke test.

Pinned evaluation dependencies are listed in the root `dependencies.repos`:

1. Livox-SDK2 `v1.3.1` commit for local, non-system installation;
2. `livox_ros_driver2` `1.2.6`, which includes MID360S support;
3. `Ericsii/FAST_LIO_ROS2` at an immutable commit, with a Handheld-scanner
   frame-name patch applied after import;
4. `Cyperstereo/CyperstereoSDK` at an immutable commit. It is the user-space
   V4L2/UVC layer for the MF287 four-camera module: the 2560x1024 YUYV stream
   carries four byte-interleaved 1280x1024 planes plus IMU and AE metadata, so
   it must not be opened as a plain colour camera. The SDK also contains the
   `ros2/src/data_cap` ROS 2 package. The 2026-11-16 pin includes
   `tool/CyperstereoView-3.0` (parameter/firmware CLI) and the latest
   SC136HGS/RK3576 ISP changes. The local checkout uses sparse-checkout to omit
   only `tool/CyperstereoView-3.0/Windows` (Windows binaries); Linux source and
   CLI are present;
5. `ethz-asl/kalibr` at an immutable commit. It is ROS 1 / `catkin` only, is
   excluded from the Humble colcon workspace, and runs through
   `tools/calibration/run_kalibr.sh` in a Noetic container.

### Camera SDK build boundary

`CyperstereoSDK` contains two independent ROS package layouts:

- `ros2/src/data_cap` — ROS 2 Humble / `ament_cmake`. **This is the only
  camera package the project builds.**
- `ros/src` — ROS 1 / `catkin` (`CyperstereoRos`). Kept for reference only;
  do not build it with colcon on Humble.
- `src/ISP` — standalone CMake target `Fast-ISP`. `data_cap` compiles the
  ISP sources it needs, so the standalone target is not built.
- `tool/CyperstereoView-3.0` — parameter/firmware utility, not a ROS package
  and not built by colcon. The local sparse checkout omits only its Windows
  binaries.

`tools/build_workspace.sh` enforces this boundary with an explicit package
allow-list (`handheld_scanner_*`, `livox_ros_driver2`,
`fast_lio`, `data_cap`).  It scans only `src/` and never builds the camera
SDK's ROS 1, sample or tool packages:

```bash
colcon build --base-paths src \
  --packages-select ... \
  --symlink-install ...
```

Always use `tools/build_workspace.sh` rather than a bare `colcon build` at
the workspace root.  The ROS 2 camera node is started with:

```bash
source install/setup.bash
ros2 run data_cap capture_image_imu
```

It publishes `/cam0..3/image_raw`, `/camN/temperature` and `/imu0`.

FAST-LIO2 is GPL-2.0 and CyperstereoSDK is GPL-3.0; both remain separate
third-party processes/libraries. Their pinned commits are evaluation
candidates, not yet the production approval decision.

The project-owned packages must not be edited to hide untracked changes inside
vendored source. Changes to upstream code require a patch file or a documented fork.

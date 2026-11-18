# Handheld-scanner

农业机器人多源融合三维采集与定位平台，目标是在 ROS 2 Humble 上完成 LiDAR、四目鱼眼相机、IMU 与 GNSS 的同步采集、三维建图和全局定位。

当前阶段：**原型验证**。项目按“方案设计 → 硬件同步 → 原型验证 → 产品化修改”四阶段推进：方案设计已完成，硬件同步基本完成（遗留 MF287 外触发固件、GNSS 天线等），当前在 EVT-0 台架上验证多传感器与算法链路；EVT-1 整机集成和产品化修改属于阶段四。目前尚无可继承的产品源码、机械图纸或电气图纸。

项目的第一份基线文档见：

- [项目理解与落地基线](docs/01_project_baseline.md)
- [待确认信息清单](docs/02_information_request.md)
- [相关成果全网检索报告](docs/03_prior_art_landscape.md)
- [高集成整机研发基准（当前有效）](docs/04_integrated_scanner_rnd_baseline.md)
- [全项目研发流程（当前执行计划）](docs/05_development_roadmap.md)
- [硬件部署清单](docs/06_hardware_deployment_checklist.md)

管理人确认的高集成整机、统一STM32时间主干、独立BMS安全域与Scanner Mainboard路线，以`04_integrated_scanner_rnd_baseline.md`版本0.4为当前最高优先级研发基准。硬件型号与接口未核验前可以通过开发板、示波器和软件完成EVT-0验证，但开发板拼接不得作为EVT-1首版整机交付，也不得直接进入结构开模或产品式PCB定板。

## 工作区结构

```text
Handheld-scanner/
├── docs/                             # 项目基线、调研与研发流程
├── src/
│   ├── handheld_scanner_interfaces/  # 整机时间与电源状态消息
│   ├── handheld_scanner_description/ # 最终坐标系与标定契约
│   ├── handheld_scanner_lidar/       # 型号无关雷达适配（当前 MID360S）
│   ├── handheld_scanner_camera/      # 型号无关相机适配（当前 MF287）
│   ├── handheld_scanner_mapping/     # FAST-LIO2选型与输出契约
│   ├── handheld_scanner_bringup/     # 唯一整机启动入口
│   ├── handheld_scanner_timesync/    # 时间同步板只读状态轮询
│   └── vendor/                       # 固定提交的第三方依赖
├── patches/                          # 第三方源码补丁（由 import 脚本应用）
├── tools/                            # 可重复构建脚本
├── build/                            # colcon生成，忽略
├── install/                          # colcon生成，忽略
└── log/                              # colcon生成，忽略
```

## 当前迭代

原型验证阶段的第一个子阶段是`v0.2雷达惯导建图`：先接入MID360S点云和内置IMU，再跑通FAST-LIO2基础建图。四目、标定、视觉融合、GNSS定位和农业场景按 P3.1–P3.6 顺序进入；Scanner Mainboard、结构与产品化修改放到阶段四，避免同时调试所有链路。

基础构建：

```bash
./tools/build_workspace.sh
source install/setup.bash
```

无实物雷达时的离线链路：

```bash
./tools/import_dependencies.sh
./tools/build_livox_sdk2.sh
./tools/build_workspace.sh
./tools/download_public_mid360.sh

bag=$(find datasets/public/driving_slam_mid360/extracted -name metadata.yaml -printf '%h\n' -quit)
./tools/run_offline_lio.sh "$bag"
```

公开数据配置仅用于算法链路验证，不是Handheld-scanner实机外参。

当前不提交未核验的Livox JSON或假外参。安装并锁定第三方驱动后，整机仍从同一入口启动：

```bash
ros2 launch handheld_scanner_bringup handheld_scanner.launch.py \
  enable_lidar:=true device_config:=/absolute/path/to/verified_mid360s.json
```

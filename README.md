# AgriSense-360

农业机器人多源融合三维采集与定位平台，目标是在 ROS 2 Humble 上完成 LiDAR、四目鱼眼相机、IMU 与 GNSS 的同步采集、三维建图和全局定位。

当前阶段：高集成整机方案与分级样机验证。项目以 Scanner Mainboard、封闭可更换电池组件、刚性传感器头和统一计算/散热结构为核心；EVT-0负责台架验证，不计为首版设备，EVT-1才是需要通过整机集成门槛的首版样机。目前尚无可继承的产品源码、机械图纸或电气图纸。

项目的第一份基线文档见：

- [项目理解与落地基线](docs/01_project_baseline.md)
- [待确认信息清单](docs/02_information_request.md)
- [相关成果全网检索报告](docs/03_prior_art_landscape.md)
- [高集成整机研发基准（当前有效）](docs/04_integrated_scanner_rnd_baseline.md)
- [全项目研发流程（当前执行计划）](docs/05_development_roadmap.md)

管理人确认的高集成整机、统一STM32时间主干、独立BMS安全域与Scanner Mainboard路线，以`04_integrated_scanner_rnd_baseline.md`版本0.3为当前最高优先级研发基准。硬件型号与接口未核验前可以通过开发板、示波器和软件完成EVT-0验证，但开发板拼接不得作为EVT-1首版整机交付，也不得直接进入结构开模或产品式PCB定板。

## 工作区结构

```text
AT-AgriSense360_ws/
├── docs/                         # 项目基线、调研与研发流程
├── src/
│   ├── agrisense360_interfaces/ # 自定义状态消息
│   ├── agrisense360_bringup/    # 统一启动、配置与话题契约
│   └── vendor/                  # 固定版本的第三方依赖
├── build/                        # colcon生成，忽略
├── install/                      # colcon生成，忽略
└── log/                          # colcon生成，忽略
```

## 当前迭代

当前版本目标是`v0.2雷达惯导建图`：先接入MID360/MID360S点云和内置IMU，再跑通FAST-LIO2基础建图。四目、GNSS融合、STM32主板和3DGS按研发流程逐阶段进入，避免同时调试所有链路。

基础构建：

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

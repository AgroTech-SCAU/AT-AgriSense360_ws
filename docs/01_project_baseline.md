# AgriSense-360 项目理解与落地基线

版本：0.1  
核验日期：2026-09-21  
状态：通用技术基线；整机形态、时间同步、BMS、电源控制与样机验收部分已由版本0.3研发基准取代

> 2026-09-30 更新：项目已确认高集成整机、统一STM32时间主干、独立BMS安全域和Scanner Mainboard路线，并明确EVT-0台架验证机不等于EVT-1首版整机。相关设计与验收以[高集成整机研发基准](04_integrated_scanner_rnd_baseline.md)版本0.3为准；本文继续保留场景、ROS 2、算法、标定与风险背景。

## 1. 项目本质

AgriSense-360 不是单一 SLAM 算法项目，而是一套可移动的多传感器测量设备。最终产品同时包含四个相互约束的系统：

1. **数据采集系统**：可靠获取原始点云、四路图像、IMU、GNSS、设备状态和标定信息。
2. **时空基准系统**：让所有测量共享可追溯的时间轴、坐标系和刚性外参。
3. **状态估计与建图系统**：输出连续局部位姿、三维地图、彩色地图和全局地理位置。
4. **工程载体**：完成供电、散热、防尘、防震、线缆固定、存储和一键运行。

正确的落地顺序是：单传感器稳定 → 同步采集 → 标定 → LIO → 视觉融合 → GNSS 全局融合 → 导航与产品化。不能一开始就同时调全部算法。

## 2. 已知目标与范围

### 2.1 目标场景

- 果园、农田和农业设施的三维数据采集；
- 枝干、地形和行间环境建模；
- 移动机器人局部定位与导航；
- 多次、长距离、带地理坐标的重复采集；
- 为点云和视觉 AI 生产带时间与位姿的数据集；
- 支持机器人安装与手持采集两种形态。

### 2.2 工作模式

| 模式 | 最小输入 | 核心输出 | 定位性质 |
|---|---|---|---|
| A 数据采集 | LiDAR、四目、两套 IMU、GNSS、状态量 | rosbag2/MCAP、标定文件、采集清单 | 不要求实时融合 |
| B LIO 建图 | LiDAR + LiDAR 内置 IMU | 局部里程计、轨迹、几何点云地图 | 连续局部坐标，会累计漂移 |
| C LIVO/彩色建图 | LiDAR + 主 IMU + 至少一路相机 | 融合轨迹、彩色点云、纹理 | 对同步和标定高度敏感 |
| D GNSS 辅助 | LIO 里程计 + 合格 GNSS/RTK + 航向来源 | map/UTM 中的全局轨迹与重复定位 | 抑制长程漂移 |

模式不是四套互不相关的软件，而应共享同一套驱动、时间戳、TF、诊断和录包基础设施。

## 3. 硬件事实核验

### 3.1 LiDAR

原始材料中的“Hesai MID360S”品牌有误。MID-360S 是 **Livox** 产品。官方参数为 200,000 点/秒、360° 水平视场、-7°~52° 垂直视场、内置 ICM40609 IMU、100BASE-TX、9~27 V 输入、典型功耗 6.5 W、低温自加热峰值可到 14 W，并支持 IEEE 1588-2008 PTPv2 和 GPS 同步。

参考：

- [Livox Mid-360S 官方规格](https://www.livoxtech.com/mid-360s/specs)
- [Livox Mid-360S 官方下载页](https://www.livoxtech.com/mid-360s/downloads)
- [livox_ros_driver2](https://github.com/Livox-SDK/livox_ros_driver2)

`livox_ros_driver2` 已明确支持 Ubuntu 22.04、ROS 2 Humble 和 Mid-360S。FAST-LIO 需要每点时间戳进行运动补偿，因此必须保留 Livox `CustomMsg` 或确认 `PointCloud2` 中的 per-point time 字段完整，不能只验证“RViz 能看到点云”。

### 3.2 四目鱼眼相机

公开产品参数显示，CyperStereo 四目模组包含四路 1280×1024、30 fps、RGB 全局快门相机和 200 Hz BMI088；接口为 USB 3.0/UVC，支持 160° 或 200° 镜头，标称相机间同步约 10 μs、相机与 IMU 小于 100 μs。

参考：

- [CyperStereo 四目模组官方页面](https://tujian.tech/products/quad)
- [CyperStereo SDK](https://github.com/Cyperstereo/CyperstereoSDK)

SDK 提供 ROS 2 Humble 构建入口，但在进入系统设计前仍需确认：

- 实物硬件/固件版本和四路图像的实际封装方式；
- ROS 消息的 topic、encoding、frame_id 和时间戳来源；
- 是否具备外部 trigger 输入，以及外触发时序、电平和曝光对应关系；
- 四目与 BMI088 的出厂外参是否可获得；
- 30 fps 时四路同时传输是否稳定、是否存在丢帧或同一 USB 控制器争用。

公开资料只证明模组内部同步，**不能据此认定 STM32 能触发该相机**。

### 3.3 计算平台

“NUC150”存在型号歧义。如果指 MINIX NUC150，其配置是 Intel N150、16 GB LPDDR5X、2.5GbE 和 M.2 SSD。Intel N150 是 4 核 4 线程、6 W 基础功耗的入门 CPU。

参考：

- [MINIX NUC150](https://www.minix.us/nuc150)
- [Intel N150 官方规格](https://www.intel.cn/content/www/cn/zh/products/sku/241636/intel-processor-n150-6m-cache-up-to-3-60-ghz/specifications.html)

该平台可作为驱动、LIO 和有限录包的验证机，但不能在未压测前承诺同时承担四路 ISP/颜色转换、无压缩录包、FAST-LIVO2、RViz 和 AI 推理。它没有适合通用 CUDA 工作负载的 NVIDIA GPU。

### 3.4 GNSS

目前只能确认轮趣 G60 是低成本 GPS/北斗定位模块。公开商品页面没有给出可核验的 RTK 频点、RTCM/NTRIP、基站/移动站、PPS、时间精度、载波解算状态或厘米级指标。因此暂时将它定义为“普通 GNSS 候选”，而不是 RTK 接收机。

如模式 D 要求厘米级重复定位，GNSS 必须至少证明：

- 双频/多频载波观测与 RTK fixed/float 状态；
- RTCM3 输入、NTRIP 或本地基站链路；
- 1PPS 与对应 UTC/GNSS 时间报文；
- `NavSatFix` 协方差、差分龄期、卫星数和 fix quality；
- 更新率和动态性能；
- 是否双天线输出绝对航向。

单天线 GNSS 在静止时不能提供车头航向。BMI088 和 ICM40609 也不能独立提供长期绝对 yaw，因此全局坐标对齐必须通过双天线航向、可靠磁航向、运动后的 GNSS 航迹，或专门的图优化来解决。

### 3.5 STM32 同步控制器

STM32 的合理职责是：

- 捕获 PPS/事件边沿并记录 MCU 计数器；
- 在硬件明确支持时产生相机触发；
- 采集电压、电流和温度；
- 控制各路电源使能与安全关机；
- 向 ROS 2 发布同步状态和 offset 诊断。

它不能仅靠一根“LiDAR Sync”脉冲使全系统获得 UTC。Mid-360S 的 GPS 同步需要符合设备协议的 PPS 与时间数据，或者使用 PTP。STM32 若作为无 GNSS 环境的本地时钟，还需要定义 MCU 时钟到 NUC 系统时钟、LiDAR 时钟和相机时钟的转换关系，并持续估计漂移。

## 4. 数据吞吐与存储边界

四路 1280×1024@30 fps 图像是当前系统最大的工程压力。

- UYVY422（2 B/px）理论原始量约 `4 × 1280 × 1024 × 30 × 2 = 314.6 MB/s`，约 1.13 TB/h；
- RGB8（3 B/px）约 471.9 MB/s，约 1.70 TB/h；
- 以上还不包含 LiDAR、IMU、GNSS、消息序列化和文件系统开销。

实际设备可能使用组合帧、降帧、ROI 或其他格式，必须用实机测量。项目需要明确三档记录策略：

1. **原始标定档**：短时、四路无损或原始数据；
2. **融合运行档**：主相机全帧，其余相机降帧或压缩；
3. **长时巡检档**：按任务需要压缩、分包和循环存储。

NVMe 选型不仅看容量，还需持续写入、温度降速、掉电保护和 TBW。建议每个 rosbag 分片，并在 metadata 中保存软件版本、标定版本、序列号、采集人、场地和时间同步状态。

## 5. 推荐系统架构

### 5.1 坐标系

遵守 REP-105，并明确所有外参方向：

```text
earth / UTM
    └── map
         └── odom
              └── base_link
                   ├── lidar_link
                   │    └── lidar_imu_link
                   ├── camera_rig_link
                   │    ├── cam0_optical_frame
                   │    ├── cam1_optical_frame
                   │    ├── cam2_optical_frame
                   │    └── cam3_optical_frame
                   ├── camera_imu_link
                   └── gnss_link
```

- `odom -> base_link`：连续、短期平滑的 LIO/LIVO 位姿；
- `map -> odom`：回环或 GNSS/global fusion 修正；
- `earth/UTM -> map`：地理坐标对齐；
- 传感器外参作为版本化静态 TF，不允许散落在多个 YAML 中且方向含糊。

### 5.2 ROS 2 接口基线

最终 topic 名称可调整，但消息语义先固定：

| 数据 | 建议 topic | 消息/要求 |
|---|---|---|
| Livox 原始点云 | `/sensors/lidar/livox` | `livox_ros_driver2/msg/CustomMsg`，保留每点时间 |
| 通用点云 | `/sensors/lidar/points` | `sensor_msgs/PointCloud2`，供可视化/下游 |
| LiDAR IMU | `/sensors/lidar/imu` | `sensor_msgs/Imu`，LIO 主 IMU |
| 四路图像 | `/sensors/camera/camN/image_raw` | `sensor_msgs/Image`，源时间戳 |
| 相机参数 | `/sensors/camera/camN/camera_info` | `sensor_msgs/CameraInfo` |
| 相机 IMU | `/sensors/camera/imu` | `sensor_msgs/Imu`，VIO/标定使用 |
| GNSS | `/sensors/gnss/fix` | `sensor_msgs/NavSatFix`，真实协方差 |
| GNSS 时间 | `/sensors/gnss/time_reference` | `sensor_msgs/TimeReference` 或自定义状态 |
| RTK 状态 | `/sensors/gnss/rtk_status` | fixed/float/age/ratio/sats |
| 同步状态 | `/system/sync/status` | 各时钟 offset、jitter、lock 状态 |
| 设备状态 | `/diagnostics` | ROS diagnostics |
| LIO 里程计 | `/localization/lio/odometry` | `nav_msgs/Odometry` |
| 注册点云 | `/mapping/cloud_registered` | `sensor_msgs/PointCloud2` |
| 全局里程计 | `/localization/global/odometry` | `nav_msgs/Odometry` |

驱动层不直接绑定算法层 topic；通过 bringup 中的 remap/adapter 适配，便于更换算法。

### 5.3 时间同步架构

推荐优先级：

1. **室外绝对时间模式**：GNSS 作为 UTC/GNSS 时间源；PPS/时间报文进入可支持的设备，NUC 通过 PPS + chrony/gpsd 或合格 PTP grandmaster 校时；Mid-360S 使用 GPS 同步或 PTP；STM32 捕获 PPS 并记录 trigger 事件。
2. **室内相对时间模式**：NUC/PTP 或 STM32 单调时钟作为本地基准，持续维护每个传感器时钟到 ROS time 的仿射关系 `t_ros = a × t_sensor + b`，不能只在启动时减一个固定 offset。
3. **退化模式**：若某设备只能用主机到达时间，则明确标记为未锁定，记录接收时间和估计误差，禁止悄悄伪装成硬同步。

每条数据需要区分：测量/曝光时刻、设备发送时刻和主机接收时刻。融合使用测量时刻。

### 5.4 定位与建图分层

```text
Livox 点云 + LiDAR IMU
          │
          ▼
     FAST-LIO2/LIO  ─────► odom -> base_link（连续局部位姿）
          │
          ├──────────────► 几何三维地图
          │
相机 ─────┴─► LIVO/离线着色 ─► 彩色点云/纹理
          │
GNSS/RTK ─┴─► Global fusion / pose graph ─► map -> odom
                                            │
                                            ├─► 地理轨迹
                                            └─► 2.5D/2D 地图转换 ─► Nav2
```

FAST-LIO2 本身应视为局部 LiDAR-惯性里程计，而不是完整的长期全局定位器。GNSS 不能简单“接入 FAST-LIO2”就自动实现模式 D；需要 `robot_localization` 双滤波结构、因子图/位姿图，或支持 GNSS 因子的专用融合器。GPS 可能跳变，因此 Nav2 的局部控制应使用连续 `odom`，全局修正放在 `map -> odom`。参考 [robot_localization 的 GPS 融合说明](https://github.com/cra-ros-pkg/robot_localization/blob/rolling-devel/doc/integrating_gps.rst)。

Nav2 也不能直接消费一张三维点云地图完成常规地面导航，还需要地面分割、障碍投影、坡度/可通行性分析以及 `OccupancyGrid` 或代价地图。

## 6. 算法与 ROS 版本兼容性

| 组件 | 上游事实 | 本项目结论 |
|---|---|---|
| livox_ros_driver2 | 官方支持 ROS 2 Humble、Mid-360S | 可作为生产前的驱动基线，但需做稳定性增强与压测 |
| CyperStereo SDK | 提供 ROS 2 Humble 示例，GPL-3.0 | 先做驱动审计、topic/timestamp/丢帧测试 |
| FAST-LIO | 官方主线文档仍以 ROS1/catkin 为主 | ROS2 使用社区移植，必须固定 fork 与 commit 并自行维护 |
| FAST-LIVO2 | 官方主线要求 ROS1/catkin；ROS2 有社区 PR/fork | 不作为首阶段承诺，先用单路相机离线验证 |
| R3LIVE | ROS1，GPLv2，商业使用需另行联系 | 作为离线彩色建图对照方案，不直接列为 ROS2 生产组件 |
| Kalibr | ROS1 工具，支持多相机、鱼眼、Camera-IMU 时空标定 | 用 Docker/独立 ROS1 环境运行，结果转换后进入 ROS2 |
| Nav2 | ROS2 原生 | 需增加 3D→2.5D/2D 可通行地图层 |

参考：

- [FAST-LIO](https://github.com/hku-mars/FAST_LIO)
- [FAST-LIVO2](https://github.com/hku-mars/FAST-LIVO2)
- [R3LIVE](https://github.com/hku-mars/r3live)
- [Kalibr](https://github.com/ethz-asl/kalibr)

FAST-LIVO2 支持 equidistant 鱼眼模型，但原始框架通常消费一路图像。四路相机不能默认等价为“四目融合”；合理的第一版是选定一台主相机参与 LIVO，其余三台同步记录和离线着色。真正四目紧耦合需要额外算法开发和性能预算。

## 7. 标定体系

所有标定结果必须包含序列号、时间、温度、软件 commit、目标板参数、残差报告和适用结构版本。

建议顺序：

1. 四台相机各自内参和畸变（鱼眼优先 `pinhole-equi`/equidistant，按实测选模）；
2. 四目 camera chain 外参；
3. camera rig 与 BMI088 的空间和时间标定；
4. LiDAR 与 LiDAR 内置 IMU 的坐标定义确认；
5. LiDAR 到主相机/相机 rig 外参；
6. `base_link` 到 LiDAR、相机 rig、GNSS 天线相位中心的机械测量；
7. GNSS 杆臂与全局航向对齐；
8. 用独立数据集验证投影误差、重力方向、点云重影和闭环误差。

Kalibr 能完成多相机与 Camera-IMU 标定，并支持 equidistant 模型；参考 [Kalibr VI 标定流程](https://github.com/ethz-asl/kalibr/wiki/Calibrating-the-VI-Sensor)。LiDAR-Camera 可评估 FAST-Calib 等工具，但必须用实际鱼眼模型和数据验证，不能只复制示例 YAML。

## 8. 机械与电控关键原则

### 8.1 机械

- LiDAR 的有效垂直视场为 -7°~52°，相机支架、GNSS 天线、手柄和线束不能大面积遮挡扫描；
- 四相机、LiDAR 和相关 IMU 应固定在同一刚性骨架上，整机再做隔振；独立软连接会使外参随振动变化；
- GNSS 天线需要尽可能开阔的上半球视野并远离 NUC、DC-DC 和高速数字线；
- IP54 与主动穿透式风道天然冲突，建议“密封传感器头 + 独立计算/电源仓”；
- USB、RJ45、天线和供电必须有应力释放、锁紧和防呆；消费级 USB 插头不能直接承担车载振动；
- 结构设计须保留标定板可视、散热、维护和序列号标识空间。

### 8.2 电源

24 V 输入后至少划分：LiDAR 电源、NUC 电源、5 V 相机/MCU/GNSS。需要反接、浪涌、过流、欠压、过温、保险/电子熔断和受控关机。Mid-360S 低温峰值可到 14 W，DC-DC 不能只按典型功耗选型。

在 NUC、SSD、相机和外设实测前，暂按 60 W 以上峰值能力留量；最终根据启动浪涌和温升测试定额。敏感 GNSS/同步信号与开关电源走线分区，避免电源纹波和地环路污染时间信号。

## 9. 当前最高风险

| 优先级 | 风险 | 后果 | 处置 |
|---|---|---|---|
| P0 | G60 不是真 RTK 或无 PPS | 模式 D 和绝对时间无法成立 | 获取手册/实测；必要时更换多频 RTK |
| P0 | 相机不支持外触发 | STM32 同步方案失效 | 获取准确硬件版本和 trigger 规范 |
| P0 | ROS2 算法依赖非官方移植 | 编译、消息和数值行为不稳定 | 固定 fork/commit，建立回放回归数据集 |
| P0 | 四目数据量超出 N150/SSD | 丢帧、录包失败、热降频 | 先做带宽/CPU/磁盘压力测试，定义记录档位 |
| P0 | 两套 IMU 职责不清 | 标定和融合数据混用 | LIO 默认用 LiDAR IMU；Camera IMU 用于 VI 标定/视觉支路 |
| P1 | 无绝对航向 | UTM/map 朝向不确定 | 双天线或轨迹对齐方案 |
| P1 | 结构遮挡 LiDAR 或外参不稳 | 地图盲区、彩色重影 | FOV 模型审查和整机刚度/振动测试 |
| P1 | GPL/商业许可未评估 | 后续交付与分发受限 | 在产品路线确定前完成许可证审查 |
| P1 | 将三维地图直接交给 Nav2 | 导航地图不可用 | 增加地面/障碍/坡度和 2D 投影层 |

## 10. 分阶段落地与验收门槛

### 阶段 0：冻结事实与接口

- 收齐实物照片、铭牌、序列号、采购链接、手册、线束和原厂 SDK；
- 确认 NUC 完整配置、GNSS 能力、相机外触发和 LiDAR 接口；
- 建立 BOM、接口控制文档、坐标系和 topic 合同。

**通过条件**：所有 P0 硬件问题有书面答案，不再用商品简称替代料号。

### 阶段 1：单设备驱动与录包

- 固定 Ubuntu/ROS、驱动 commit、固件和网络/USB 配置；
- 独立运行 LiDAR、四目、两套 IMU、GNSS、STM32；
- 统计频率、延迟、丢包、CPU、内存、USB、网络、磁盘和温度。

**通过条件**：连续运行 2 h 无节点退出、无不可解释丢帧，诊断与 rosbag 可复现。

### 阶段 2：统一时间与标定

- 先完成室内相对同步，再完成 GNSS 绝对同步；
- 记录每类时间戳与 offset/jitter；
- 完成多相机、Camera-IMU、LiDAR-Camera 和杆臂标定。

**通过条件**：同步和重投影指标由实测报告给出；重复装配后外参变化在预算内。

### 阶段 3：FAST-LIO2 几何基线

- 用固定数据集验证 ROS2 移植；
- 调整 IMU 噪声、盲区、体素和外参；
- 做静止、直线、闭环、起伏地面和树行测试。

**通过条件**：无发散，静止漂移、闭环误差、CPU 和实时率达到定义指标。

### 阶段 4：视觉与彩色地图

- 先单主相机 FAST-LIVO2/离线着色；
- 再评估其余三相机对覆盖和质量的增益；
- 对逆光、枝叶摆动、低纹理、运动模糊做专项测试。

**通过条件**：彩色重影与轨迹性能优于或不劣于几何基线，实时性可接受。

### 阶段 5：GNSS 全局融合

- 建立 local odom 与 global map 双层定位；
- 验证 RTK fixed/float/失锁/重锁和树冠遮挡；
- 做多次同路线重复采集的地图对齐。

**通过条件**：GNSS 跳变不传入局部控制；全局误差、重定位时间和退化行为满足任务要求。

### 阶段 6：导航与整机工程化

- 生成 2.5D/2D 可通行地图并接入 Nav2；
- 完成热、尘、振动、供电波动、异常掉电和线缆测试；
- 提供一键启动、健康检查、数据导出和故障日志。

## 11. 初始技术决策

在新证据出现前采用以下基线：

- ROS 2 Humble 作为系统总线；ROS1 算法/标定工具放入隔离容器，不污染主机依赖；
- 首个可交付版本优先完成模式 A 和 B；模式 C、D 在硬件能力验证后进入；
- FAST-LIO 的主 IMU 使用 Mid-360S 内置 ICM40609；BMI088 服务于相机链和 VI 标定；
- 第一版 LIVO 只使用一路主相机，四路全部保留在数据采集模式；
- GNSS 未证明 RTK/PPS 前，不对外宣称“厘米级”和“全球统一硬同步”；
- 原始数据、派生数据、标定和软件版本必须可追溯。

## 12. 对项目完成的定义

项目完成不等于“RViz 有点云”或“算法 demo 能跑”。完整交付至少包含：

- 冻结的 BOM、结构图、电气图、线束图和同步时序图；
- 可重复安装的 Ubuntu/ROS 2 环境和锁定依赖；
- 全部驱动、bringup、TF、配置、diagnostics、录包和导出工具；
- 标定工具链、结果、报告和重复标定流程；
- LIO、视觉融合、GNSS 融合与导航的独立验收报告；
- 典型农业场景数据集和自动回归测试；
- 操作、故障处理、维护和数据管理文档；
- 开源许可证与商业使用边界说明。

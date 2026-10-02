# AgriSense-360 高集成整机研发基准

版本：0.4
生效日期：2026-09-30  
决策来源：项目管理人 2026-09-24 沟通结论、当前研发要求及 2026-09-29 高集成整机修订批准  
状态：当前有效研发基准

> 本文优先级高于 `01_project_baseline.md` 中与整机形态、时间同步、BMS 和电源控制相关的旧描述。出现冲突时，以本文为准。

## 1. 产品定义

AgriSense-360 不再按“多个独立模块临时拼接”或“把若干成品盒装进一个大箱子”的形态设计，而应形成一台可独立工作的高集成三维扫描设备：插入一块电池、按键开机后，BMS、控制板、NUC、LiDAR、四目相机和 GNSS 按既定时序启动，ROS 2 能获取全部传感器、时间源、电池和整机状态。

“高集成”指统一结构、线束、供电、时间、状态机和软件入口，不代表将电池安全、DC/DC、时间同步和计算全部强行做在一块 PCB 上。内部仍采用清晰的安全域与功能分层：

1. 电池包与 BMS：封闭可更换的电芯安全域；
2. Scanner Mainboard：统一时间、触发、供电时序、状态检测与内部接口；
3. 可选固定电源子板：仅在EMI、散热或维修评审证明需要时承载DC/DC和大电流功率器件；
4. NUC计算单元：ROS 2、录包、建图和系统管理；
5. 刚性传感器头：Livox MID360S、CyperStereo MF287和GNSS天线。

第一版整机优先使用成熟电池包和现成 BMS。Libre Solar BMS C1 与 foxBMS 2 仅作为后续自研 BMS 的硬件、CAN、状态机和故障管理参考，第一版不同时承担“自研同步板”和“自研 BMS”两项高风险工作。使用成熟模块不等于允许模块散装：BMS 必须归入电池组件，NUC、主板和传感器必须归入统一机械、电气和软件架构。

### 1.1 高集成的判定

高集成按“完整设备”而不是按 PCB 数量判定。首版整机至少必须实现：

- 单一整机外壳与统一承力/散热结构；
- 单块可更换电池、单一主按键、统一状态指示；
- 统一内部供电、数据、时间同步和锁紧线束；
- 统一充电、维护和调试接口区域；
- 统一上电、运行、录制、故障和安全关机状态机；
- 统一 ROS 2 启动入口、设备身份、版本与诊断；
- 传感器头作为刚性标定总成，日常使用不改变外参。

允许内部存在电池/BMS、Scanner Mainboard、计算单元和传感器等可维护组件；不允许以外露开发板、飞线、独立适配器、外置 Hub、外置同步盒或多个独立开关构成所谓“整机”。

### 1.2 样机名称与边界

- `EVT-0 台架验证机`：允许使用 STM32 开发板、临时转接板和实验线束，用于确认接口、同步、功耗和算法；它不属于首版完整设备，也不能作为高集成成果验收。
- `EVT-1 首版整机`：必须使用定制 Scanner Mainboard 或固定成套的主板组件，完成统一结构、内部线束、散热、接口、一键开关机和 ROS 2 管理；它才是本项目所称的“第一版样机”。

EVT-0 是降低 EVT-1 返板风险的前置验证活动，不得因台架功能跑通而取消 EVT-1 的整机集成要求。

## 2. 冻结的总体架构

```text
电池包 + 现成 BMS
        │ CAN/状态
        ▼
Scanner Mainboard（Control / Time Sync）
        ├── 内置/配套电源域：NUC/LiDAR/CAM/GNSS/FAN
        ├── GNSS PPS + GPRMC 输入
        ├── MID360S PPS + GPRMC 输出
        ├── MF287 Trigger × 1（FPGA内部同步四目）
        ├── MF287 Master Exposure Feedback × 1
        └── USB/UART/CAN → NUC

MID360S ─Ethernet─┐
MF287 ─USB3/UVC─┼── NUC / ROS 2 Humble
GNSS数据 ─UART/USB┤
控制板状态 ─USB──┘
```

### 2.1 整机物理总成

EVT-1 收敛为以下四个物理总成，而不是若干独立设备的集合：

1. **刚性传感器头**：Livox MID360S、CyperStereo MF287、GNSS 天线及固定长度线束；
2. **计算与控制核心**：NUC、Scanner Mainboard、必要的内部 USB Hub/以太网交换功能和统一散热结构；
3. **可更换电池组件**：电芯、现成 BMS、保险和电池侧连接器组成封闭组件；
4. **整机结构件**：外壳、承力骨架、机器人/手持安装接口、风道、按键、指示灯和统一接口面板。

上述总成必须有明确安装基准、连接器、拆装顺序和版本号。临时扎带、热熔胶、裸露接线端子和无法复现的手工飞线不得进入 EVT-1。

### 2.2 Scanner Mainboard 归并要求

EVT-1 以一块 `Scanner Mainboard` 作为设备电气中心，其核心必须包含或直接承载：

- STM32H7/G4、TCXO、PPS捕获与GPRMC处理；
- MID360S PPS/GPRMC输出、MF287单路Trigger输出及Master Exposure反馈输入；
- 预留额外Trigger/事件IO，但MF287正常工作不要求四路外部触发扇出；
- USB/UART/CAN、调试与产测接口；
- NUC、LiDAR、Camera、GNSS、Fan的使能、PGOOD和故障采集；
- 传感器、电池、NUC和内部数据连接的锁紧连接器；
- 板卡温度、关键电压和负载电流监测。

DC/DC、eFuse和大电流负载开关优先与主板形成统一设计。若因EMI、散热、安规或维修必须采用独立电源板，则只能作为与主板固定配套的电源子板：具有定义好的板间连接、安装孔位、接口协议、版本兼容和屏蔽/接地方案，不得使用通用降压模块散装拼接。

EVT-1 不允许以通用 STM32 开发板加多块转接板代替 Scanner Mainboard。GNSS 接收模块可以作为经选型冻结的板载模块或锁定式 mezzanine，但不得作为机外悬挂模块。

### 2.3 NUC与内部数据连接

- EVT-0 可以使用完整 NUC 小主机；EVT-1 应优先采用 NUC 主板级安装或可验证的嵌入式安装，接入统一底板、风道和电源时序；
- 若保留 NUC 原装机壳，必须通过体积、重量、散热和振动评审，不能默认接受“箱中箱”；
- 相机所需 USB Hub、网口扩展或交换功能必须内置并由主板统一供电、复位和监测；
- 设备正常工作不得依赖机外 USB Hub、交换机、同步盒或传感器电源适配器。

### 2.4 对外接口收敛

EVT-1 对外只保留完成任务所需的接口类别：

- 可更换电池接口与统一充电接口；
- 一个主开关机按键和统一状态指示区域；
- 机器人供电/数据接口（若任务需要）；
- 集中的维护、调试和数据导出接口区；
- GNSS 天线接口仅在外置天线方案确认后保留。

LiDAR、四目相机、GNSS接收机、同步器和NUC之间的接口均为机内接口，不得在正常使用时暴露为需要用户逐一连接的多组线缆。

传感器暂定：

- CyperStereo MF287四目鱼眼RGB+IMU相机：单设备USB3/UVC，外触发2.8–3.3 V、最高30 Hz、0.5 ms高电平，内部FPGA同步四路曝光并给图像/IMU打硬件时间戳；
- Livox MID360S，具体序列号、固件、线束和同步针脚仍须按实物冻结；
- 能输出 1PPS 与 GPRMC/GNRMC 的 GNSS，RTK 能力另行核验；
- NUC 计算平台；
- 带独立 BMS 的电池包。

## 3. 统一时间架构

### 3.1 基本原则

所有传感器统一以 STM32 控制板的连续时间轴为设备时间主干。GNSS 不是另一套工作模式，而是 STM32 本地时间的外部校准源。无论 GNSS 是否存在，相机 Trigger 和送往 LiDAR 的同步信号都由同一个受控时基生成。

时间必须区分三种语义：

- `GNSS_LOCKED`：时间直接受有效 GNSS PPS + 有效日期/时间报文约束；
- `HOLDOVER`：曾经锁定 UTC，当前依靠本地振荡器维持，UTC 为估计值且不确定度随时间增长；
- `LOCAL_SYNC`：从未获得有效 UTC，只保证设备内部同步，绝不能对外宣称为真实 UTC。

MID360S 数据包中的同步类型只能说明设备接受了相应格式的同步输入，不能单独证明当前时间来自真实 GNSS。ROS 2 和数据集元数据必须额外记录上述时间源状态。

### 3.2 GNSS 有效

```text
GNSS 1PPS ──► STM32定时器输入捕获
GNSS GPRMC ─► 校验和/状态/日期/时间/连续性检查
                    │
                    ▼
              本地时钟驯服
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
MID360S PPS + GPRMC      MF287 Trigger × 1
```

进入 `GNSS_LOCKED` 不能只看到 PPS 边沿，至少应同时满足：

- NMEA 校验和正确；
- RMC 状态、日期和 UTC 时间有效；
- PPS 与 RMC 秒号关系连续；
- 连续若干秒无跳秒、乱序或异常周期；
- GNSS 模块自身时间/定位状态满足设定条件。

### 3.3 GNSS 暂时丢失

从 `GNSS_LOCKED` 进入 `HOLDOVER` 时：

- 不停止输出 PPS、GPRMC 和 Camera Trigger；
- 不允许时间回退或突然跳变；
- 使用外部 TCXO 和锁定阶段估计的频率误差维持时间；
- 持续输出 holdover 时长、预计误差和振荡器状态；
- GNSS 恢复后先验证，再以限速调整或相位连续方式重锁，禁止直接 step 当前时间。

“最后一次校准参数”不能只保存在软件变量中。若 TCXO 不可压控，固件需要用相位累加器、定时器小数分频/周期抖动等方式补偿频率；若采用 VCTCXO，则需要 DAC 与闭环控制。TCXO 标称 ppm、温漂、老化和板级热环境必须进入 holdover 误差预算。

### 3.4 完全没有 GNSS

系统进入 `LOCAL_SYNC`：

- STM32 自主产生连续 1PPS、GPRMC/GNRMC 和 Camera Trigger；
- 可使用 RTC/上次保存值建立一个合规的合成历元；
- 对 MID360S 的输出必须满足设备格式和时间范围要求；
- `utc_status=INVALID`，数据只能解释为同一设备内的相对同步时间。

若设备在 `LOCAL_SYNC` 录制过程中首次获得真实 GNSS，真实 UTC 与合成历元之间可能相差很大。此时不能同时满足“立刻切到真实 UTC”和“时间戳不跳变”。基准策略是：

1. 录制开始前获得 GNSS：允许在 ARM/RECORD 前完成对时；
2. 录制过程中首次获得 GNSS：本段继续保持 LOCAL 时间，同时发布 LOCAL→UTC 映射；
3. 需要切换为真实 UTC：关闭当前 bag/数据段，在明确的会话边界重新建立时间轴。

从 `HOLDOVER` 恢复 GNSS 不属于上述首次大偏差场景，应平滑重锁。

### 3.5 MID360S 时间输入约束

当前以 Livox 官方 MID-360 GPS Time Synchronization 文档作为预设计输入；原理图冻结前必须再以MID360S实物手册、固件和线束复核：

- PPS 与 UART 均为 3.3 V TTL 时可直接进入相应引脚；不同电平必须转换；
- UART：9600 baud、8 data bits、no parity，实际实现按 8N1；
- 报文：GPRMC 或 GNRMC；
- 相邻 PPS 上升沿：900–1100 ms，有效目标 1000 ms；
- PPS 高电平：大于 1 μs，官方建议 10–200 ms；
- PPS 斜率：建议大于 1 V/μs；
- GPRMC 在 PPS 上升沿后 0–900 ms 开始，官方建议 0–430 ms；
- 9600 baud 下完整 GPRMC 发送时间约 70 ms；
- MID-360 GPS 时间范围为 2000-01-01 至 2037-12-31。

以上必须在原理图评审、固件单测和示波器验收中逐项覆盖。MID360S 的针脚、固件和同步模式支持必须使用对应实物手册再次确认，不能仅凭 MID-360 公开资料直接定板。

## 4. Scanner Mainboard（含 Control / Time Sync）

`Scanner Control / Time Sync` 是 Scanner Mainboard 的核心功能域，不再作为一只独立外置同步盒。时间敏感电路与大电流电源电路可以在 PCB 上分区，必要时也可采用固定主板+电源子板结构，但两者在机械、电气、版本和产测上必须作为一个主板组件管理。

### 4.1 MCU 选择

STM32G4 与 STM32H7 均保留为候选，但在原理图冻结前完成选型评审：

- G4：定时器/HRTIM强、功耗和板级复杂度较低，适合以时间与电源控制为主的控制板；
- H7：算力、RAM和高速接口裕量更大，适合增加以太网/PTP或复杂在线估计，但功耗、EMI和固件复杂度更高。

第一版不按“性能越高越好”选择 MCU，而按所需定时器通道、输入捕获、UART、CAN、USB、ADC、看门狗、启动时间和开发成熟度确定。

MCU开发板仅用于EVT-0接口验证。进入EVT-1前必须完成主板原理图、PCB、BOM、连接器定义、测试点和板级产测方案，不能把开发板永久封装进整机代替定制主板。

### 4.2 必备接口

最低接口：

- GNSS PPS IN × 1：输入保护、施密特整形、可选电平转换；
- GNSS UART IN × 1，建议同时预留 GNSS UART TX/配置；
- MID360S PPS OUT × 1：独立缓冲与测试点；
- MID360S GPRMC UART OUT × 1：3.3 V TTL、9600/8N1；
- MF287 Trigger OUT × 1：2.8–3.3 V兼容、不高于30 Hz、高电平0.5 ms，由硬件定时器生成；
- USB Device 到 NUC，第一版采用 CDC/自定义二进制协议；
- CAN × 1，用于 BMS/整机状态；
- SWD/JTAG、Boot、复位、串口日志和关键测试点；
- EN_NUC、EN_LIDAR、EN_CAM、EN_GNSS、EN_FAN；
- 各路 PGOOD/FAULT 与电压、电流、温度采样。

强烈建议增加：

- MF287 Master Exposure Feedback IN × 1：证明实际曝光而不是只证明 Trigger 输出；
- 预留Trigger/Event IO × 3或以上：供后续外设、产测或差分驱动使用；
- PPS/Trigger 回环输入：用于产测和在线自检；
- NUC PWRBTN 控制与 `shutdown_ready` 输入；
- 外部参考时钟/TCXO 监测；
- 连接逻辑分析仪的统一测试座。

### 4.3 MF287触发与时间戳

MF287是一台内含四路成像和IMU的设备，不是四个独立相机。Scanner Mainboard只向MF287输出一路硬件Trigger，由其FPGA在设备内部实现四路同步曝光。Trigger必须由同一设备时间主干的硬件定时器生成，不得使用普通线程或中断临时翻转GPIO。

已确认的输入条件为2.8–3.3 V、最高30 Hz、高电平0.5 ms。主目提供Exposure信号，从目不单独提供；图像时间戳为FPGA记录的曝光结束时刻，同时提供曝光时长，标准测量时刻按 `t_mid = t_end - exposure_duration / 2` 计算。图像与IMU共用FPGA时间系统，但FPGA时间轴与STM32设备时间的偏移/漂移关系仍需通过Trigger事件和SDK实测建立。

每次Trigger产生单调递增的`trigger_count`。相机驱动应读取FPGA硬件帧号/时间戳并对应该计数；帧号、丢帧行为、时间戳分辨率/回绕周期和Master Exposure信号电气定义仍为P0待验证项。

## 5. BMS 与电源管理

### 5.1 边界

BMS 独立承担：

- 单体电压、总电压、电流和电芯温度测量；
- 过压、欠压、过流、短路、充放电过温保护；
- 均衡；
- SOC/SOH（若现成产品提供）；
- 主保护开断。

Scanner Mainboard不得绕过BMS的安全保护，只通过CAN或其他可验证接口读取状态和请求工作模式。

Scanner Mainboard的电源域或固定配套的电源子板承担：

- 宽输入 DC/DC；
- 各负载 eFuse/负载开关；
- 分路限流、反接、浪涌、过温保护；
- 负载侧电压、电流和 PGOOD/FAULT；
- 接收主板控制逻辑的EN信号。

电池串数（6S/8S/12S）、化学体系、容量、持续/峰值电流和连接器尚未冻结，必须根据全部负载实测功耗、续航、DC/DC效率和运输安全要求决定。

### 5.2 第一版策略

- 使用现成电池包与成熟 BMS，但 BMS 必须与电芯、保险和电池连接器形成封闭可更换电池组件；
- 整机只连接电池组件的电源与状态接口，不在机箱内散装裸露电芯、BMS和临时接线端子；
- 若 BMS 无 CAN，可通过其可用接口读取，或第一版只读取总压/电流并保留 CAN；
- Libre Solar BMS C1 用于参考 BQ76952、采样、功率路径、CAN/UART/I2C和开源PCB；其16串/100 A定位不能直接视为本设备的最终选型；
- foxBMS 2 用于参考状态机、故障分级、CAN/DBC、SOC/SOE/SOH/SOF和测试方法，不直接照搬汽车级整套硬件。

### 5.3 一键开关机时序

建议上电状态机：

```text
OFF → CONTROL_BOOT → BMS_CHECK → GNSS/TIME_ACQUIRE
    → NUC_ON → NUC_READY → SENSOR_RAILS_ON
    → SYNC_ARMED → RECORD_READY/RUNNING
```

建议关机状态机：

```text
SHUTDOWN_REQUEST → 停止录包/关闭bag分片 → SSD同步
    → NUC shutdown_ready → 相机/LiDAR断电
    → NUC断电 → 控制板低功耗待机
```

NUC 关机必须有软件握手和超时策略，不能按键后直接切断 SSD 电源。硬故障、BMS保护和用户强制长按属于独立紧急路径，应记录断电原因。

## 6. 固件基线

固件至少拆分为：

- `time_input`：PPS捕获、NMEA接收和有效性检查；
- `clock_servo`：相位/频率估计、holdover误差模型；
- `time_output`：MID360S PPS/GPRMC生成；
- `camera_trigger`：硬件定时器、计数器和反馈捕获；
- `power_fsm`：上电、运行、正常关机和故障状态机；
- `bms_can`：BMS状态、限值和故障；
- `telemetry`：USB/UART/CAN协议；
- `diagnostics`：看门狗、复位原因、温度、电源和事件日志；
- `bootloader/config`：版本、序列号、参数校验与安全升级。

状态机不得使用阻塞延时完成电源时序；所有超时、状态转换和故障恢复需要可记录、可回放、可单元测试。

NUC 与控制板第一版建议使用带版本号、长度、消息ID、序号、时间和 CRC 的二进制协议，由 ROS 2 `scanner_control_driver` 转换为消息。USB CDC 可传状态，但不能把 USB 数据到达时刻当成微秒级 PPS 边沿；精确事件时间必须在 STM32 内捕获后连同计数器上报。

## 7. ROS 2 状态接口

至少发布：

| Topic | 建议消息 | 内容 |
|---|---|---|
| `/system/time_sync/status` | 自定义消息 + diagnostics | 时间源状态、UTC有效性、PPS锁定、holdover时长、相位误差、频率修正、预计误差 |
| `/system/time_sync/events` | 自定义消息 | PPS计数、trigger计数、MCU捕获时刻、输出通道状态 |
| `/system/power/status` | 自定义消息 + diagnostics | 各电源轨、PGOOD、FAULT、开关机状态 |
| `/battery/status` | `sensor_msgs/BatteryState` | 电压、电流、温度、SOC、健康状态 |
| `/diagnostics` | `diagnostic_msgs/DiagnosticArray` | LiDAR、相机、GNSS、控制板、BMS和存储健康状态 |

状态字段至少包含：

```text
time_source: GNSS_LOCKED | HOLDOVER | LOCAL_SYNC | FAULT
utc_status: VALID | ESTIMATED | INVALID
pps_locked: bool
holdover_seconds: uint32
estimated_clock_error_ns: int64/uint64
trigger_count: uint64
exposure_feedback_count: uint64
camera_clock_mapping_valid: bool
camera_clock_offset_ns: int64
camera_clock_drift_ppm: float64
gnss_rmc_valid: bool
lidar_sync_reported: bool
```

在线系统不得使用 ROS `/clock` 冒充设备硬件时间。`header.stamp` 应表示测量/曝光时间；主机接收时间单独用于诊断。

## 8. 机械与整机集成

- MID-360与四目相机固定在同一刚性标定骨架上；隔振放在整机与载体之间；
- 传感器骨架必须定义机械基准、定位方式和装配扭矩；正常更换电池、搬运和安装不得改变相机-LiDAR外参；
- GNSS天线保持开阔上半球视野，并远离DC/DC、NUC和高速线束；
- 同步板与GNSS/PPS信号区远离大电流开关节点；
- 高速数据线、电源线和PPS/Trigger线束分层布置；
- PPS/Trigger/GPRMC线缆使用锁紧连接器、明确地参考和应力释放；
- 内部线束必须有编号、长度、线径、屏蔽/接地、连接器和固定点定义，并可按图纸重复生产；
- NUC、主板和功率器件共享经过计算与实测验证的散热底板/风道，禁止仅靠外壳内部自然堆放；
- 保留测试点、固件升级口、标定板视场和维护空间；
- 整机统一按键、状态灯/蜂鸣器和可识别的故障状态。

高集成整机仍要保证传感器、NUC、电池和控制板可维护更换，不能用不可拆封装换取外观上的“一体化”。

EVT-1结构评审至少应包含：整机尺寸和重量、重心、安装刚度、跌落/碰撞风险、振动、风道、最高器件温度、防尘防泼溅路径、线束应力、维护拆装时间及传感器视场遮挡。IP54是后续设计目标，未完成相应验证前不得宣称已经达到该防护等级。

## 9. 样机阶段与验收

### 9.1 EVT-0台架验证机

EVT-0只用于降低原理图和整机设计风险，可以采用开发板、临时电源和实验线束，但必须完成：

1. 验证MID360S、MF287、GNSS、NUC和BMS的真实接口、电平、功耗与启动行为；
2. 产生MID360S PPS + GPRMC和MF287单路同步Trigger；
3. 跑通GNSS锁定、holdover和local sync三个时间状态；
4. 证明MF287 Trigger来自硬件定时器，并验证其内部四目同步曝光；
5. 完成示波器、端到端时间戳、浪涌功耗和热测试报告；
6. 冻结EVT-1所需连接器、线束、电源预算和Scanner Mainboard输入条件。

EVT-0完成不代表“首版设备完成”，不得作为高集成整机交付。

### 9.2 EVT-1首版整机

EVT-1必须完成：

1. 使用定制Scanner Mainboard或通过评审的固定主板+电源子板组件，移除功能性开发板和通用降压模块；
2. 将BMS封装在可更换电池组件内，由主板统一完成NUC、LiDAR、Camera、GNSS和Fan的时序控制；
3. MID360S、MF287和GNSS天线形成刚性传感器头，完成可复现装配和外参标定；
4. NUC、主板、内部Hub/交换功能和线束全部归入统一外壳、散热和维护结构；
5. 实现一块电池、一个主按键、统一状态指示、统一充电与维护接口；
6. ROS 2读取时间源、同步、电源和电池状态，并能录制MID-360点云/IMU、四目图像与GNSS数据；
7. 一键启动后自动进入可采集状态；正常关机能够停止录包、落盘并安全关闭NUC；
8. 完成示波器、端到端同步、持续运行、散热、振动风险和整机功耗报告；
9. 输出原理图、PCB、BOM、结构图、内部线束图、接口定义、装配说明、固件和ROS 2版本清单。

EVT-1不要求：自研BMS量产板、极限holdover指标、四目实时紧耦合、全农业算法或完整IP等级认证。上述功能可以后续迭代，但不能用来降低整机集成门槛。

### 9.3 高集成放行门槛

下列条件全部满足后，EVT-1才允许标记为“完整、高集成度设备”：

- 正常工作不依赖外置同步盒、USB Hub、交换机、DC/DC或传感器电源适配器；
- 外部看不到开发板、裸BMS、飞线、杜邦线或临时接线端子；
- 用户无需逐一给相机、LiDAR、GNSS和NUC接线或开机；
- 内部线束全部锁紧、编号、固定并有可复现图纸；
- 电池、传感器头、计算控制核心和整机结构均有明确维护边界；
- 任一正常可维护操作不会无意改变相机-LiDAR刚性外参；
- 整机具有唯一序列号，能够报告硬件、固件、标定和ROS 2软件版本；
- 连续运行测试期间无过温、反复掉线、存储损坏或非预期复位。

任何一项未满足时，只能标记为“集成开发样机”，不能宣称首版高集成整机已经完成。

### 9.4 示波器验收

至少测量并保存波形/原始数据：

- GNSS PPS IN 与 STM32捕获/输出关系；
- MID360S PPS OUT 的周期、高电平、斜率和抖动；
- GPRMC开始时刻、发送时长、内容和校验和；
- MF287 Trigger的周期、脉宽、电平和抖动；
- Trigger与MID360S PPS的固定相位关系；
- Trigger与MF287 Master Exposure反馈的延迟和稳定性；
- GNSS断开前后、holdover期间和重锁过程；
- 电源上电、掉电和各路PGOOD时序。

首版暂定工程目标（供应商接口确认后冻结）：

- 相同状态下Trigger周期抖动不大于1 μs；
- Trigger高电平保持0.5 ms，频率不高于30 Hz；
- 端到端相机曝光与LiDAR时间残差先达到1 ms级并给出统计分布；
- GNSS暂失与恢复过程中设备时间不回退；
- holdover分别测试10 min、30 min、60 min并报告漂移，不在TCXO选型前虚构长期精度。

### 9.5 端到端验收

示波器证明的是电信号，最终还必须证明测量时间：

- 相机：Trigger → Exposure/Strobe反馈 → 图像硬件帧号/时间戳；
- LiDAR：输出PPS/GPRMC → 数据包`timestamp_type`/时间戳 → ROS消息；
- ROS 2：trigger_count与图像帧、LiDAR包、bag时间关系；
- 人为制造相机丢帧、GNSS断开和NUC重启，检查是否误配帧或时间回退。

## 10. 与软件版本计划的关系

软件下一版本仍保持小步目标：

> 完成 MID360S 与内置 IMU 接入，跑通 FAST-LIO2 基础建图。

硬件同步链路可在EVT-0中并行使用开发板和示波器推进，但在MID360S单传感器链路、MF287端到端触发/时间戳、GNSS输出规格、负载浪涌和NUC关机接口未验证前，不冻结EVT-1 Scanner Mainboard。软件小步推进不降低EVT-1的整机集成要求。

雷达先行阶段必须位于同一AgriSense-360工作空间、统一启动入口和最终话题/TF约定内，不建立日后再拼接的独立雷达工程。后续MF287、GNSS与Scanner Mainboard以设备配置增量接入；软件包的职责分层不等同于物理模块拼装。

## 11. P0 待确认项

- MID360S序列号、固件、连接器、时间同步针脚及其与MID-360公开协议的差异；
- MF287硬件帧号/丢帧行为、Master Exposure反馈电气定义、FPGA时间戳分辨率/回绕/漂移；
- MF287四路相机ID与160°/200°镜头对应关系、出厂标定文件和机械尺寸图；
- GNSS准确型号、1PPS电平、RMC时序、失锁时行为、RTK状态与CAN/UART协议；
- NUC输入电压、峰值功耗、PWRBTN和安全关机接口；
- 现成电池/BMS的串数、化学体系、持续/峰值电流和通信协议；
- TCXO频率、稳定度、压控能力、温漂和老化；
- 相机、LiDAR和NUC启动浪涌及各电源轨额定值；
- 四路相机的数据接口带宽、内部USB Hub/以太网交换拓扑及NUC可用端口；
- NUC采用主板级安装还是保留原装机壳，以及对应散热、振动、保修和维护边界；
- 整机目标尺寸、重量、续航、安装方式和外部接口数量；
- MID-360对RMC状态`V`和合成时间的实际接受行为，必须实测，不能假定。

## 12. 参考基线

- [HKU-MARS LIV_handhold](https://github.com/xuankuzcr/LIV_handhold)：STM32同步、相机触发、线束、CAD及驱动修改；
- [HKU-MARS LIV-Eye / LIV_handhold_2](https://github.com/hku-mars/LIV_handhold_2)：MID-360、相机、硬同步器和FAST-LIVO2复现；
- [Livox MID-360 GPS Time Synchronization](https://github.com/Livox-SDK/livox_wiki_en/blob/master/source/tutorials/new_product/common/time_sync.rst)：PPS/GPRMC电平与时序；
- [Livox MID-360 Communication Protocol](https://github.com/Livox-SDK/livox_wiki_en/blob/master/source/tutorials/new_product/mid360/livox_eth_protocol_mid360.md)：时间戳类型、诊断与同步状态；
- [Libre Solar BMS C1](https://github.com/LibreSolar/bms-c1)：开源BMS硬件与通信参考；
- [Libre Solar BMS C1 Manual](https://libre.solar/bms-c1/manual/manual.pdf)：连接、安全与接口；
- [foxBMS 2](https://github.com/foxBMS/foxbms-2)及[官方文档](https://docs.foxbms.org/)：状态机、CAN/DBC、故障管理和状态估计。

## 13. 对旧方案的修正摘要

1. 两套同步模式改为一个STM32连续时间主干和三个有明确语义的时间状态；
2. STM32从“可选同步器”升级为整机时间、触发、电源时序和状态管理核心；
3. 本地合成时间必须标记为非UTC，不能只凭LiDAR同步类型宣称真实UTC；
4. 增加首次LOCAL→UTC切换的会话边界策略，避免时间戳跳变；
5. MF287改为单路硬件Trigger，四目同步由设备内部FPGA完成，同时保留Master Exposure反馈与硬件帧号要求；
6. BMS保持独立安全域，第一版使用现成方案；
7. Scanner Mainboard与可选电源子板边界明确，NUC采用可握手的正常关机；
8. EVT-0以示波器、电气接口和端到端测量时间验证为重点，EVT-1同时接受整机集成验收，不追求一次完成所有融合算法；
9. 明确区分EVT-0台架验证机与EVT-1首版整机，开发板拼接不再计为首版设备；
10. EVT-1以Scanner Mainboard、封闭电池组件、刚性传感器头和统一计算散热结构形成完整设备；
11. 增加外置模块禁止项、内部线束与文档要求，以及高集成整机放行门槛。

# 硬件部署清单

适用：Handheld-scanner（原 AgriSense-360）`v0.2 雷达惯导建图`。
部署目标：把扫描板、GNSS 和雷达按新命名接入，并确认 `/system/time_sync/status` 正常发布。

## 1. 命名迁移对照

改名前后的对应关系，旧脚本、旧笔记、旧规则一律按右列替换。

| 旧 | 新 |
|---|---|
| `agrisense360_*` | `handheld_scanner_*` |
| `scanner_control_driver` | `handheld_scanner_timesync` |
| `agrisense360.launch.py` | `handheld_scanner.launch.py` |
| `/dev/agrisense-*` | `/dev/handheld-scanner-*` |
| `70-agrisense-serial.rules` | `70-handheld-scanner-serial.rules` |
| 仓库 `AT-AgriSense360_ws` | 仓库 `Handheld-scanner` |

话题名、frame 名、四份契约 YAML 和 `msg` 定义不变，已有 bag 与外部脚本不受影响。

## 2. 串口别名部署

### 2.1 删除旧规则

```bash
sudo rm -f /etc/udev/rules.d/70-agrisense-serial.rules
```

### 2.2 安装新规则

**必须在工作区目录内执行**（或把路径写成绝对路径），否则 `cp` 会报"没有那个文件或目录"。

```bash
cd ~/github_work/AT-AgriSense360_ws

sudo cp src/handheld_scanner_timesync/config/70-handheld-scanner-serial.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger --action=change --subsystem-match=tty
```

### 2.3 验证

```bash
ls -l /etc/udev/rules.d/70-handheld-scanner-serial.rules
ls -l /dev/handheld-scanner-*
```

期望结果：

| 别名 | 设备 | VID:PID |
|---|---|---|
| `/dev/handheld-scanner-timesync` | 扫描板（STM32 USB CDC） | `0483:5740` |
| `/dev/handheld-scanner-gnss` | Septentrio mosaic-G5 USB1，NMEA/命令 | `152a:8231`，接口 00 |
| `/dev/handheld-scanner-gnss-aux` | Septentrio mosaic-G5 USB2，SBF/调试 | `152a:8231`，接口 02 |

别名只在设备插入时生成。**设备没插时查不到是正常状态**，不代表规则没装好。

## 3. 设备接入

| 设备 | 物理接口 | 主机侧表现 | 是否必须 |
|---|---|---|---|
| 扫描板（TimeSyncV2） | USB（数据线） | `0483:5740` → `ttyACM*` → `/dev/handheld-scanner-timesync` | v0.2 可选，验证时间同步时必接 |
| GNSS 接收机 | USB | `152a:8231` → `/dev/handheld-scanner-gnss`(-aux) | v0.5+ |
| MID360S 雷达 | 网口 UDP | 不出 tty，话题 `/livox/lidar`、`/livox/imu` | v0.2 必需 |
| MF287 四目相机 | USB 视频 | 出 `/dev/video*`，不是 `ttyACM` | v0.3 |

接入顺序：先插扫描板确认别名，再插 GNSS；雷达走网络，最后核对 IP 与 UDP 端口。

> 扫描板的 USB CDC 端口是独占的。厂商 web console 打开时节点只能打开失败并重试，**启动节点前先关闭 console**。

## 4. 启动与验证

```bash
source /opt/ros/humble/setup.bash
source install/setup.bash

# 只读轮询扫描板
ros2 launch handheld_scanner_bringup handheld_scanner.launch.py enable_control:=true

# 另开终端
ros2 topic echo --once /system/time_sync/status
```

节点日志应出现：

```text
waiting for TimeSyncV2 on /dev/handheld-scanner-timesync @ 115200 8N1
opened /dev/handheld-scanner-timesync
```

`TimeSyncStatus` 的关键字段：

| 字段 | 含义 |
|---|---|
| `time_source` | 时间源状态（LOCAL / GNSS / HOLDOVER / FAULT） |
| `trigger_count`、`pps_count` | **本次上电后**的累计值，不是持久设备标识 |
| `lidar_sync_reported` | 雷达输出是否已 arm |
| `detail` | 板端原始状态，含 `state`、`mode`、`firmware` |
| `header.stamp` | 主机发布时刻，**不是**板端时间 |

## 5. 故障排查

| 现象 | 原因 | 处理 |
|---|---|---|
| `lsusb` 里没有 `0483:5740` | 线是充电线 / 端口无供电 / 板子未上电 | 换数据线、换直连 USB 口、看板子指示灯 |
| 有 `0483:5740`，但没有 `ttyACM*` | `cdc_acm` 未绑定 | `sudo modprobe -r cdc_acm && sudo modprobe cdc_acm` |
| 有 `ttyACM*`，没有 `/dev/handheld-scanner-*` | 规则未加载或未触发 | `sudo udevadm control --reload-rules` 后 `sudo udevadm trigger --action=add --subsystem-match=tty` |
| 旧别名 `/dev/agrisense-*` 还残留 | `change` 事件清不掉旧链接 | 拔插设备，或 `trigger --action=remove` 再 `--action=add` |
| 节点反复 `cannot open` | 厂商 web console 占着端口 | 关闭 console；或用 `fuser /dev/handheld-scanner-timesync` 查占用 |
| GNSS 别名异常 | 系统另有 `70-septentrio-g5.rules` 匹配同一 VID:PID | `cat /etc/udev/rules.d/70-septentrio-g5.rules` 核对是否冲突 |

## 6. 软件侧检查

```bash
./tools/build_workspace.sh
colcon test --packages-select handheld_scanner_timesync
colcon test-result --verbose

ros2 pkg list | grep handheld_scanner
```

## 7. 验收标准

- [ ] `/etc/udev/rules.d/` 下只剩 `70-handheld-scanner-serial.rules`，无 `70-agrisense-serial.rules`
- [ ] 插入扫描板后 `/dev/handheld-scanner-timesync` 存在且指向 `ttyACM*`
- [ ] 无 `/dev/agrisense-*` 残留
- [ ] `ros2 launch handheld_scanner_bringup handheld_scanner.launch.py enable_control:=true` 能打开端口
- [ ] `/system/time_sync/status` 持续发布，`detail` 中出现 `firmware=20261020_CFG1`（或板端实际版本）
- [ ] `colcon test --packages-select handheld_scanner_timesync` 全部通过

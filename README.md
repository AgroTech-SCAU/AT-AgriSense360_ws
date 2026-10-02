> [!IMPORTANT]
> ## 仓库初始化
>
> 本仓库由 **AgroTech Repository Template** 创建
>
> 项目负责人 / 仓库管理员首次创建仓库后，请完成以下初始化，完成后请阅读 .github/CONTRIBUTING.md 和 .github/rulesets/README.md：
>
> - [ ] 点击绿色按钮 `Code` → `Clone using the web URL.` → `git clone <仓库 URL>`，将仓库克隆到本地
> - [ ] 填写本 README 中的项目基本信息、环境、构建与运行方式
> - [ ] 填写 [`docs/plan.md`](docs/plan.md)，明确当前目标与下一步
> - [ ] 确认默认分支为 `main`
> - [ ] **公开仓库**：进入 `Settings → Rulesets → Rulesets → New ruleset → Import a ruleset`
> - [ ] 导入克隆到本地仓库中的 [`.github/rulesets/main-protection.json`](.github/rulesets/main-protection.json)
> - [ ] 加载后点击页面最下方的绿色按钮 `Create`，确认 Ruleset 已启用并作用于 `main`
>
> GitHub Free Organization 的 Rulesets 仅适用于公开仓库；若本仓库为私有仓库且 Settings 中没有 Rulesets 入口，跳过 Ruleset 导入即可
>
> **初始化全部完成后，请删除本段“仓库初始化”提示**

# <项目名称>

> 一句话说明项目解决什么问题

## 当前状态

- **状态：** 开发中
- **最新稳定版本：** 暂无
- **当前开发计划：** [`docs/plan.md`](docs/plan.md)

> 首次形成可复现的稳定版本后，再创建 Git Tag + GitHub Release，并将本 README 更新为该稳定版本的完整使用说明

## 1. 项目简介

说明：

- 项目用途
- 主要能力
- 适用场景
- 当前边界 / 不支持的内容

## 2. 环境要求

### 软件

- OS：
- ROS / Runtime：
- Compiler / Python：
- 关键依赖：

### 硬件（如适用）

- 主控：
- 传感器：
- 执行器：
- 接口：

## 3. 安装

```bash
# 示例
```

## 4. 构建

```bash
# 示例
```

## 5. 快速开始

```bash
# 最小可运行示例
```

预期现象：

- ...

## 6. 配置说明

| 配置项 | 默认值 | 说明 |
| --- | --- | --- |
| `<param>` | `<value>` | ... |

## 7. 目录结构

```text
.
├── README.md
├── docs/
│   └── plan.md
└── ...
```

## 8. 文档

- `docs/plan.md`：项目规划（必须）
- `docs/architecture.md`：系统架构（如有）
- `docs/interface.md`：接口说明（如有）
- `docs/deployment.md`：部署说明（如有）
- `docs/calibration.md`：标定说明（如有）
- `docs/troubleshooting.md`：故障排查（如有）

## 9. 常见问题

### 问题 1

现象：

原因：

处理：

## 10. 版本与发布

正式稳定版本使用 **Git Tag + GitHub Release** 发布

版本历史见：<Releases 链接>

## 11. 维护者

- Maintainer：`@GitHub-ID`

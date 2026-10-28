<img src="plugins/kai-icloud-calendar/assets/icon.svg" width="128" alt="Kai iCloud Calendar">

# Kai ChatGPT Plugins

用于 ChatGPT / Codex 的工具与使用流程插件，让常用任务可以直接通过对话完成。

[English](README.en.md) · [GitHub 仓库](https://github.com/kmjskai/kai-chatgpt-plugins) · [问题反馈](https://github.com/kmjskai/kai-chatgpt-plugins/issues)

## 插件

| 插件 | 能力 | 平台 |
| --- | --- | --- |
| [Kai iCloud Calendar](plugins/kai-icloud-calendar/README.md) | 查看日历、查询日程、按明确确认的安排创建单个事件 | macOS 本地运行 |

## 安装与快速开始

需要支持本地插件源和本地 MCP 的 Codex 客户端。下载完整目录或克隆本仓库，然后在目录根部运行：

```sh
codex plugin marketplace add .
codex plugin add kai-icloud-calendar@kai-chatgpt-plugins
```

在桌面客户端中新建本地会话，选择 **Kai iCloud Calendar**，输入：

> 列出我的日历，并查看未来七天的日程。

插件列表没有刷新时，可以刷新插件源或重新打开客户端。安装不要求提供 Apple 密码。

## 系统要求与权限

- macOS 14 或更新版本、Apple Silicon Mac；当前随包助手仅支持 arm64。
- Node.js 20 或更新版本，且客户端能在 PATH 中找到 `node`。
- 所需账户已经配置在 macOS 日历中，并由系统完成同步。
- 按首次使用提示，授予 **Kai Apple Calendar Helper** 日历完全访问权限。

插件需要在 Mac 的本地会话中运行；手机和纯网页会话不能直接运行本机助手。构建目标为 macOS 14，实际兼容性仍需在目标系统上验证。

## 更新、卸载与恢复

更新插件源后重新安装对应插件，并新建会话。保留旧版完整目录可以用于恢复。

```sh
codex plugin remove kai-icloud-calendar@kai-chatgpt-plugins
codex plugin marketplace remove kai-chatgpt-plugins
```

卸载插件不会删除日历或日程，也不会自动撤销系统授权。可在“系统设置 → 隐私与安全性 → 日历”管理助手权限；同步异常应先检查 macOS 日历中的账户状态。

## 数据、网络与隐私

日历插件通过系统 EventKit 访问本机日历，不自行登录 iCloud，也不运行独立的日历云服务。它可以访问 EventKit 暴露的 iCloud 等账户，而非仅限某一个账户。

请求得到的日历内容会返回当前 AI 客户端，受该客户端的数据处理规则约束。插件没有额外的日历内容日志或分析服务；系统账户同步、客户端通信和系统签名检查可能需要网络。

## 已知限制与反馈

当前支持读取和创建单个非重复事件，不支持更新、删除或创建重复事件。创建前需要明确确认日历和事件详情；写入结果不明确时，不要直接重试，应先查询是否已经保存。

向插件提供者反馈时，请说明客户端版本、macOS 版本、插件版本和错误信息。无需提供密码、访问令牌或完整的私人日程。

## 从源码构建

随包提供日历 MCP 与 Swift 助手的构建源码。安装 Xcode Command Line Tools 后，参照 [构建说明](docs/building.md) 构建；日常使用不需要 Swift 编译器。

## 许可证

本仓库自有代码、文档、配置和随包的日历 Skill 使用 [Apache License 2.0](LICENSE)。随包组件的归属和许可见 [NOTICE](NOTICE)。

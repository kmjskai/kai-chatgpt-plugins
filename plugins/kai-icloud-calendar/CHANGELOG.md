# Changelog

## 2026.10.0

- 在对话中列出 Mac 日历，按日期、日历和标题查询日程。
- 经明确确认后创建单个非重复事件，并核对保存结果。
- 需要 macOS 14+、Apple Silicon 和 Node.js 20+。
- 暂不支持更新、删除、创建重复事件或独立移动端访问。

### 安装与校验

下载本 Release 的 `kai-chatgpt-plugins-2026.10.0.zip` 并完整解压，在目录根部运行：

```sh
codex plugin marketplace add .
codex plugin add kai-icloud-calendar@kai-chatgpt-plugins
```

首次读取时，允许 Kai Apple Calendar Helper 访问日历。需要已同步账户的 Mac 本地会话；手机和纯网页会话无法运行本机助手。最低目标为 macOS 14，实际验收系统见仓库说明；不把构建目标当作该系统的实机验收。

随包附有 `SHA256SUMS.txt` 和 `release.json`，分别用于核对归档摘要和版本／公证回执。安装问题可在本仓库 Issues 反馈，请勿提供密码或完整私人日程。

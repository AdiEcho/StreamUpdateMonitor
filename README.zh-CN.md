# StreamUpdateMonitor
[English](README.md) | 简体中文

![License](https://img.shields.io/github/license/adiecho/StreamUpdateMonitor)

StreamUpdateMonitor 是一个可以监控各种流媒体平台更新的多功能工具。

## 配置
StreamUpdateMonitor 有一个示例配置文件 `config/config.sample.yaml`，可以用来设置监控工具。

请通过将文件复制为 `config/config.yaml` 并填写相关字段来设置功能。

## 功能
- [x] **自定义监控频率**：用户可以为每个平台设置自定义监控频率，以便在更新当天或检测到新内容时立即收到通知
- [x] **自定义通知**：用户可以设置自定义通知设置，通过电子邮件、短信或其他消息服务接收通知（基于 Apprise）

## TODO
- [ ] 添加更多流媒体平台的支持
- [ ] 每个平台可以自定义通知设置

## 警告
该项目仍在开发中，配置文件可能会发生变化。请报告您遇到的任何问题。

## 贡献
你可以通过提交 PR 来贡献代码。

## 许可证
本项目基于 [AGPL-3.0](LICENSE) 许可证



# Android 自动记账项目总结

## 任务概述
构建基于 NotificationListenerService 的自动记账应用，支持微信/支付宝。

## 关键技术
1. **NotificationListenerService**: 用于捕获通知栏消息。
2. **Regex Parsing**: 本地解析金额和类型。
3. **Room Database**: 本地持久化存储。
4. **Android 13/14 权限**: 处理 `POST_NOTIFICATIONS` 和 `BIND_NOTIFICATION_LISTENER_SERVICE`。

## 踩坑经验
- Android Sandbox 环境下 `Invoke-WebRequest` 即使使用 `-UseBasicParsing` 也可能因临时文件权限失败。建议用户本地运行构建脚本。
- 华为手机需额外处理电池优化白名单。

## 交付物
- 完整源代码 (Kotlin)
- 一键构建脚本 (PowerShell)

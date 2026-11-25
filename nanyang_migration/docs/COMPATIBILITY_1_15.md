# 1.15 兼容性调查

目标为 **1.15.2**。这是调查时 Modding Co-op 仓库最新列出的 1.15 系列版本，该仓库 11 月 19 日提交了 1.15.2 的完整生成日志。Steam 公告、Steam 新闻 API、Paradox 论坛和 Wiki 的 HTTPS 请求均被环境代理拒绝。未取得 Dev Diary #194/#196 或官方 Hotfix 正文，因此无法独立确认是否另有更新的正式补丁。选择 1.15.2 为候选版的精确兼容号，避免承诺其余 1.15.x。

[1.15.0 Breaking Changes](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/changes_breaking.md) · [1.15.0 Features](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/changes_features.md) · [1.15.0 脚本差异](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/changes_script_docs.md) · [1.15.1](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/tree/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.1) · [1.15.2](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/tree/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2)

| 变化 | 调查与适配 |
| --- | --- |
| Journal 当次结局 | 旧 `complete`、`fail`、`invalid` 由 outcome 替代；零个 outcome 是新版类型文档明确支持的永久条目形式。采用显式 country context 和新版 country pin 字段。未拿到 1.15.2 原版永久日志文件。 |
| 日志组 | 1.15 为组要求 illustration，允许 themed，context 由组提供并可覆盖。继续引用 `je_group_foreign_affairs`，由原版提供其插画。组 ID 在旧版快照确认，在 1.15.2 数据中的存在仍待本地核查。 |
| Scripted Button | 新增可选标签、图标、展示成本及自动完成。沿用主动按钮，添加全局锁的可用性说明和点击后的复查。 |
| Scope / Effects / Triggers | 1.14 与 1.15 的相关变更以 1.15.0 差异及最终日志核对。移动效果与相关人口/State 迭代器仍存在。1.15.2 新增 conclude_journal_entry，不需要调它。 |
| 本地化 | 保留 UTF-8 BOM 与双语目录，使用直接 Script Value/变量引用，没有嵌套含 `$loc$` 的字符串参数，故无需新增 `\|q`。 |
| 文化/国家 | `min`、`yue`、`hakka`、`han`、`CHI` 来自 1.13.11 明确标记的历史数据。1.15.2 日志确认 country_definition 与内战 origin 链接。1.15 修改过中国重统一日志，1.15.2 修改过中国起始国家历史，缺少原文可核对新版中央政府变量写入。保留旧条件，**这五个 ID 和变量并未用 1.15.2 游戏数据逐项确认**。 |
| 地图 | 对照了 1.15.0 公开新增/重命名清单，设计中的 30 个 ID 没有列在改名项里。1.15.1 修改印度、东亚和印尼地图文件，公开差异只列出文件名。仍须用原版新数据验证全部 ID，保留设计地理范围，不作推测性替换。 |
| Launcher 和依赖 | 保留本地 Mod JSON 格式、ID 和目录，改为明确的 1.15.2 标签、候选版本号。无自定义 DLC 检查及依赖。Launcher 加载尚待实测。 |
| 其余破坏性变更 | 本项目未定义船型、战争目标、从属类型、基因、军队动员选项、游戏目标和脚本进度条，无相关字段需要迁移。 |

`alcaras/v3ref` 公开 main 仍标 1.13.11，`tjysdsg/Victoria-3-files` 公开分支最高可见 1.9.0，CWTools 最新可取提交为 11 月 5 日且未标 1.15.2 的引擎编译结果。它们是历史快照或辅助类型说明。保留历史数据摘要，另记录目标版日志摘要。已安装游戏可用以下命令仅导出 ID 与 SHA-256：

```sh
python3 tools/audit_native.py --game-data "/path/to/Victoria 3/game" --game-version 1.15.2
```

复核目标版原生文档调用面：

```sh
python3 tools/audit_native.py --digest /path/to/Modding-Digests
```

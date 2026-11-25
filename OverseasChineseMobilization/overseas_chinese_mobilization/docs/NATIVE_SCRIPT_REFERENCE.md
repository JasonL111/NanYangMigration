# 原生脚本证据

目标 **Victoria 3 1.15.2**。重新访问了官方 Steam 公告、Steam News API、Paradox 新闻与论坛、Victoria 3 Wiki。环境代理拒绝这些 HTTPS 连接，因此未把未读取的官方公告标为已确认。2026年11月25日重新拉取 Modding Co-op 后，最新公开 1.15 目录仍为 **1.15.2**，该提交日期为11月19日。无法独立排除更晚的官方热修。

- [1.15.2 生成的引擎日志，提交 0e94618](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/tree/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs)
- [1.15 Breaking Changes](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/changes_breaking.md) · [Journal 类型](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/types/journal_entries.md) · [Scripted Button 类型](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/types/scripted_buttons.md) · [Script Value 类型](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/documentation/types/script_values.md)
- [CWTools Victoria 3 辅助规则，提交 bec1001](https://github.com/cwtools/cwtools-vic3-config/tree/bec10017635de6dac01525210b4c932db0ce1c40/config) · [v3ref 数据，提交 bd8e3f7，1.13.11](https://github.com/alcaras/v3ref/tree/bd8e3f7da313a57d0509559d59cff7617cc49513)
- [旧版原版脚本参考，1.9.0 快照](https://github.com/tjysdsg/Victoria-3-files/tree/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game)

| 接口 | 作用域和证据 | 本 Mod 的使用 |
| --- | --- | --- |
| `country_definition`、`cd:`、`civil_war_origin_country`、`is_player` | 1.15.2 `event_targets.log` 的 Country 链接和 `triggers.log` 的玩家判定 | `cd:CHI` 及内战来源判定。原版 `chinese_central_government` 的写入示例见旧版 `warlord_china_events.txt`（指向 `c:BEI`）；1.15.2 核实了 `has_global_variable`、`global_var` 和 Country 关系接口。1.15 修改清单列出该原版脚本，未取得当前文件内容，故该指针只在存在且匹配当前国家时识别。 |
| `country_tier`、`is_country_alive` | 1.15.2 `triggers.log`，Country；CWTools `enum[country_tier]` 包含 `hegemony` | 排除 `country_tier = hegemony`，不比较国力排名。历史游戏国别文件中 BHT 等使用 `tier = hegemony`。 |
| `culture_percent_country` | 1.15.2 `triggers.log`，Country，`target = cu:dixie value >= 0.2`（0–1） | 四个原生比例比较仅作宽松预筛。CWTools 提供参数化数值链接提示，1.15.2 生成日志没有记录其数值读取写法；正式脚本不依赖该链接求和。 |
| `every_scope_pop`、`total_size`、`total_population` | 1.15.2 `effects.log` 与 `triggers.log`；Country POP 枚举，POP 总大小，Country 总人口。后者有单列的含附庸版本；CWTools 将 `total_size` 和 `total_population` 列为数值；原生 Script Value 模板支持列表汇总 | Country 范围逐 POP 加总人数。总大小不同于日志中的 `workforce`、`dependents` 单项。分母用不含附庸的总人口。 |
| `multiply`、`ceiling`、`>=` | 1.15 Script Value 模板和 CWTools 比较规则 | 分母乘精确写法 `0.4` 再向上取整，避免对比例做除法或显示舍入。等价于用整数比较 `5×四文化人数 ≥ 2×总人数`，脚本无需把总人口扩大五倍。引擎内部极值和精度仍需本地验证。 |
| `cu:han`、`cu:min`、`cu:yue`、`cu:hakka` | 1.15.2 `event_targets.log` 记录 `cu:` 和 POP `culture`；四个 ID 由 1.13.11 `cultures.json` 交叉核对 | 仅使用这四个 ID，无文化特质泛化。1.15 原版定义文件未取得；可用仓库的 `tools/audit_game_data.py` 对安装版本核对 ID。 |
| `country_has_primary_culture`、`add_primary_culture` | 1.15.2 生成日志确定 Country 输入和 Culture 目标，effect 将文化加入现有主流文化 | `every_country` 将作用域切到目标国，使用 `add_primary_culture = cu:han` 后再检查。旧版原版 `common/scripted_effects/00_scripted_effects.txt:221` 有相同赋值；未取得 1.15.2 的原版调用文件。 |
| `any_country`、`every_country`、`trigger_if`、`trigger_else` | 1.15.2 `triggers.log` 与 `effects.log` | 按钮查询全球是否有目标，执行重新校验。条件分支确保不合格国家不做逐 POP 精算。 |
| `save_scope_as`、`save_scope_value_as`、`trigger_event` | 1.15.2 `effects.log`，以及 `data_types_script.txt` 的 `TopScope.GetValue(Arg0)` | 在 Country 内累计并保存确认数，事件正文以 `[SCOPE.GetValue('ocm_confirmed_recognitions')\|0]` 显示本次值。选项无效果。 |
| Journal / Scripted Button | 1.15 类型和 Breaking Changes 证实 country context、零 outcome、按钮 `visible/possible/effect` 与 `ai_chance` | 复用原版外交事务组，组插画由游戏提供。没有自定义 Journal GUI、完成条件或额外 DLC。组在安装版可与文化 ID 一并核对。 |
| 事件图 `event_image = { texture = "…" }` | CWTools 的 `config/events/events.cwt` 记录原生块与纹理文件路径，历史原版事件有此块 | 事件引用原创 `gfx/event_pictures/ocm_guild_hall.dds`。使用4:3的1280×960 DXT1/BC1 DDS，已解码并验文件头。这是本 Mod 的资源规格，未查得 1.15.2 硬性尺寸或压缩要求，也未测试弹窗裁切。 |

原画由图像工具生成，位于源码 `assets/ocm_guild_hall.png`。重做纹理可从项目根目录运行：

```sh
magick assets/ocm_guild_hall.png -colorspace sRGB -resize 1280x960 -alpha off \
  -define dds:compression=dxt1 -define dds:mipmaps=0 \
  overseas_chinese_mobilization/gfx/event_pictures/ocm_guild_hall.dds
```

在安装游戏的电脑核对国别、文化与日志组：

```sh
python3 tools/audit_game_data.py "/path/to/Victoria 3/game"
```

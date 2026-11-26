# Victoria 3 原生脚本参考

2026 年 11 月 26 日复查后，可取得的 1.15 正式补丁资料最新为 **1.15.2**。Modding Co-op 将 1.15.2 标为 Release，完整引擎生成日志见 11 月 19 日的提交。Steam 公告、Paradox 论坛和 Wiki 均返回代理 403，本次无法通过官方公告独立排除更晚的热修。Launcher 兼容版本填为精确的 1.15.2。[1.15.2 Release Digest](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/discord.md) · [Steam 官方公告页](https://steamcommunity.com/app/529340/announcements/)

## 政治力量和认同度

1.15.2 生成的 Modifier Types 注册表列出了以下六个键，均为 `interest_group` Mask。通过 Country 的 `add_modifier` 挂载含带组 ID 键的静态修正，键中的 ID 决定对应利益集团。固定点数走 `_approval_add`，政治力量率走 `_pol_str_mult`。[1.15.2 Modifier Types](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/modifiers.log#L7669-L7700) · [1.15 Modifier 类型与传递规则](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/types/modifier_type_definitions.md)

| 目标 | 政治力量 | 认同度 |
| --- | --- | --- |
| 地主 | `interest_group_ig_landowners_pol_str_mult = -0.50` | `interest_group_ig_landowners_approval_add = -5` |
| 知识分子 | `interest_group_ig_intelligentsia_pol_str_mult = 0.25` | `interest_group_ig_intelligentsia_approval_add = 5` |
| 实业家 | `interest_group_ig_industrialists_pol_str_mult = 0.25` | `interest_group_ig_industrialists_approval_add = 5` |

较早的原版脚本提供两类交叉证据。1.9.0 的佃农法把 `0.25` 用于地主政治力量，城市化事件在国家上施加含实业家认同度 `2` 的静态修正。v3ref 1.13.11 的佃农法仍将 `0.25` 显示为 `+25%`，该事件的认同度显示为 `+2`。1.15.2 的生成日志确认这两类原生键仍在。具体的叠加、下限与修正后的 Clout 由原版计算，未测定最终数值。[1.9.0 土地改革法](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/common/laws/00_land_reform.txt#L55-L66) · [1.9.0 城市化事件](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/events/urbanization_events.txt#L370-L376) · [1.9.0 静态修正](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/common/static_modifiers/02_event_modifiers.txt#L1271-L1274) · [v3ref 1.13.11](https://github.com/alcaras/v3ref/tree/bd8e3f7da313a57d0509559d59cff7617cc49513)

## 调用与类型证据

下表以 1.15.2 引擎生成文档及 1.15 类型文档为主要依据。CWTools 提交 `bec1001` 补充了引擎日志中未展开的参数结构。可取得的完整原版文件为历史版本，引用时标明版本。1.15.2 的原版定义文件和引擎行为需用安装版核对。[引擎文档固定提交 0e94618](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/tree/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs) · [CWTools 固定提交 bec1001](https://github.com/cwtools/cwtools-vic3-config/tree/bec10017635de6dac01525210b4c932db0ce1c40/config)

| 接口与输入 | 文档依据和本 Mod 的使用 |
| --- | --- |
| `country_definition`、`cd:`、`civil_war_origin_country` | 1.15.2 的 scope links 确认 Country → Country Definition 与 Country → Country。以 `cd:CHI` 匹配中国定义或直接内战来源。匹配关系不读取政权名称。[1.15.2 Scope Links](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/event_targets.log#L1076-L1095) |
| `chinese_central_government` | 旧版原版《重统一中国》读取 `global_var:chinese_central_government ?= this`，军阀事件写入 Country。1.15.2 确认 `global_var` 和 `has_global_variable`，1.15.0 修改清单仍列出这两个原版文件。现行写入条件未取得，脚本仅在原版变量确实指向当前国家时接受该分支。[1.9.0 重统一日志](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/common/journal_entries/00_reunify_china.txt#L24-L31) · [1.9.0 军阀事件](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/events/warlord_china_events.txt#L453-L463) · [1.15.0 变更文件](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/changes_files.md) |
| `has_law`、`is_player`、`is_country_alive` | 1.15.2 Country triggers。 `has_law` 接受 Law Type scope，`law_type:law_monarchy` 有原版实例。玩家与有效国家用原生布尔判定。[1.15.2 Triggers](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/triggers.log) · [1.9.0 君主制实例](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/common/laws/00_governance_principles.txt#L121-L132) |
| `year >= 1861`、`ig:ig_landowners`、`ig_clout >= 0.20` | `year` 读取当前游戏年，可直接使用 `>=`。 `ig:` 由 Country 取集团。1.15.2 的 `ig_clout` 示例为 `>= 0.2`，输入是 Interest Group，占比单位为 0–1。先检查地主 scope 存在，再做含边界的比较。[年份触发器](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/triggers.log#L17861-L17865) · [Clout 触发器](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/triggers.log#L13719-L13724) · [集团 Scope](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/event_targets.log#L375-L379) |
| `add_modifier`、`has_modifier` | 1.15.2 确认两个接口支持 Country，查询键为 `common/static_modifiers`。CWTools 的 `add_modifier` 块和 duration 枚举包含 `years`。代码用 `years = 20`，再确认容器已挂载。二十年的实际到期日、加载后剩余时间和政治面板变化仍要在游戏里确认。[原生挂载](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/effects.log#L330-L332) · [原生查询](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/triggers.log#L13098-L13104) · [CWTools 效果格式](https://github.com/cwtools/cwtools-vic3-config/blob/bec10017635de6dac01525210b4c932db0ce1c40/config/effects.cwt#L105-L123) · [时长单位](https://github.com/cwtools/cwtools-vic3-config/blob/bec10017635de6dac01525210b4c932db0ce1c40/config/enums.cwt#L1-L7) |
| `set_global_variable`、`global_var:`、`has_global_variable`、`remove_global_variable` | 1.15.2 引擎日志列出无输入作用域的全局变量接口。设置值可为 scope 或 bool，`days` 可选。临时记录存 Country 且限期，实施记录存无期限的布尔值。全局存储设计独立于国家对象，普通保存重载与卸载重装结果要用 1.15.2 存档确认。[设置](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/effects.log#L41990-L41998) · [引用](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/event_targets.log#L693-L696) |
| Journal Entry 和 Scripted Button | `context = country`、`possible`、`is_shown_when_inactive` 及 `outcome` 源于 1.15 类型。1.15 日志组要求 `illustration`，这里复用原版内政组 `je_group_internal_affairs` 的组插图，旧版原版组 ID 可查。按钮使用 Country 的 `visible`、`possible`、`effect` 和 `ai_chance`。[1.15 破坏性变更](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/changes_breaking.md) · [日志类型](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.1/types/journal_entries.md) · [按钮类型](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/types/scripted_buttons.md) · [1.9.0 原版组 ID](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/common/journal_entry_groups/00_journal_entries.txt#L47-L49) |
| `trigger_event`、事件时限及选项 | 1.15.2 日志确认按当前 scope 触发事件，1.15 日志类型有 `popup = yes` 示例。CWTools 的 `country_event`、`duration`、`default_option` 记录了块结构。1.9.0 原版历史鼓动者事件有 `duration = 3` 及默认选项，历史 `NEvents` 定义以月计事件时限。两个选项各自清理记录，超时结果和临时期限的运行仍须实测。[1.15.2 原生效果](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/effects.log#L42446-L42451) · [CWTools 事件类型](https://github.com/cwtools/cwtools-vic3-config/blob/bec10017635de6dac01525210b4c932db0ce1c40/config/events/events.cwt) · [1.9.0 事件实例](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/events/agitators_events/historic_agitator_events.txt#L15-L58) · [1.9.0 事件定义](https://github.com/tjysdsg/Victoria-3-files/blob/0e8b62590c36bc9fdd2c8cba3cb5dda255092656/game/common/defines/00_defines.txt#L1489-L1493) |

## 事件画与本地化

事件用原生 `event_image = { texture = "gfx/event_pictures/ssr_reform_council.dds" }` 直接引用独立纹理，不需要注册另一个 illustration 定义。原创画以 4:3 裁幅，源 PNG 为 1448×1086，实际 DDS 为 1280×960，压缩采用 DXT1/BC1。尺寸和压缩是本 Mod 的选型，1.15.2 的强制格式与实际弹窗裁切未找到可核实的说明。日志使用内政组的原版横幅。1.15 文档记录原版组横幅为 1108×200，属另一种资源。[CWTools 事件纹理块](https://github.com/cwtools/cwtools-vic3-config/blob/bec10017635de6dac01525210b4c932db0ce1c40/config/events/events.cwt#L113-L124) · [1.15 Journal 插画变更](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/changes_breaking.md#journal-entry-group-illustration)

源 PNG 在仓库的 `dev/self_strengthening_reform/assets/`，从仓库根目录可复做 DDS。

```sh
magick dev/self_strengthening_reform/assets/ssr_reform_council.png \
  -colorspace sRGB -resize 1280x960 -alpha off \
  -define dds:compression=dxt1 -define dds:mipmaps=0 \
  self_strengthening_reform/gfx/event_pictures/ssr_reform_council.dds
```

两种语言均为 UTF-8 BOM。日志通过 `ssr_je_reform_reason` 提供说明，按钮使用 `name` 与 `desc`，事件标题、正文与选项指向独立本地化键。文本使用直接引用和普通换行转义。

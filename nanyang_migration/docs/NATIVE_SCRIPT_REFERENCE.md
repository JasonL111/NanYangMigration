# 原生脚本依据 · Victoria 3 1.15.2

主依据是 Modding Co-op 仓库提交 `0e94618d6a1b1599d4c78cc074282598de4d59b2`。下表“引擎日志”指对应版本生成的原生脚本文档，经社区归档。类型文档使用同提交的 1.15.0 类型差异和当前文档，另检查了 1.15.1、1.15.2 更新。SHA-256 在 [reference_ids.json](reference_ids.json) 中。

- [1.15.2 引擎日志](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/tree/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs)
- [Journal 类型原生模板](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/types/journal_entries.md)
- [Button 类型原生模板](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/types/scripted_buttons.md)
- [Script Value 原生模板](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/documentation/types/script_values.md)

| 接口与版本依据 | 作用域、参数与文档用例 | 维护决策与验证边界 |
| --- | --- | --- |
| `move_partial_pop`，1.15.2 effects.log | POP → 实际 state。引擎示例 `state = s:STATE_TUSCANY.region_state:TUS`，另示例 `population = 1000` 和 `population_ratio = 0.2`。省略数值参数的写法也存在。注记迁入后失业，部分职业和不允许的奴隶职业可变更。 | 使用数量形式；目标由已保存的 state 引用给出。生成日志未明确参数单位、数值取整、两个参数合用规则、保存 state/动态输入的解析类型和时序。CWTools `bec10017635de6dac01525210b4c932db0ce1c40` 列出 State Scope 与 Script Value，属于辅助资料。独立实机诊断分别试常数、动态值、比例、全量。 |
| `move_pop`，1.15.2 effects.log | POP → state，整 POP 原生移动。 | 不能满足任意分配额，正式流程继续使用部分移动。 |
| `total_size` / `workforce` / `dependents` / `state_population`，1.15.2 triggers.log | POP 总大小、劳动力、家属分别有数值比较接口。State 有总人口比较接口。原生例 `total_size >= 3000`、`workforce >= 1000`、`dependents >= 2000`。 | 动态数值用途与样本来自类型文档及辅助 CWTools。正式读数用两州逐 POP 合计，避免直接以州总计缓存来结账。POP 合计的即时更新仍有待实测。 |
| `every_scope_pop` / `random_scope_pop` / `every_scope_state` / `random_scope_state`，1.15.2 effects.log | Country/State 可遍历 POP；State Region 可遍历/随机选取实际 State。均支持 `limit`。原生 Script Value 模板明确支持迭代统计。 | RC3 逐个本国 State 进入原生 POP 遍历，按固定文化 ID 筛选。目的地仅访问指定地理域，所有有拥有者的分割 State 都加入候选。安全枚举失效 POP 引用的引擎行为须实测。 |
| `add_to_list` / `every_in_list`，1.15.2 effects.log | 原生例 `add_to_list = name`、`every_in_list = { list = name … }`。事件链内局部引用。 | RC1 的配对依赖该接口。RC2 改用原生实时枚举和原来源州标记，移动的 POP 或继承标记的拆分 POP 不能以落地州通过来源筛选。 |
| `save_scope_as` / `save_scope_value_as`，1.15.2 effects.log | 保存任意当前 scope 或数值为 `scope:<key>`。Journal 原生模板展示保存引用与事件。 | 转移前保存国家、两州和请求量。调用移动后仅通过已保存的州/国家读取，不再依赖源 POP 的大小或位置。 |
| `set_variable` / `change_variable` / 移除操作，1.15.2 effects.log / event_scopes.log | 生成日志宣称 POP 可存变量，但实机 error.log 对 POP 的 `has_variable` 明确报 `This scope doesn’t support variables`。以实机观察为准。 | RC4 将工作额度放在国家，接收状态放在目的州，POP 不调用变量接口。州按文化记录接收状态。 |
| `set_global_variable` / `change_global_variable` / `has_global_variable` / `remove_global_variable`，1.15.2 effects/triggers.log | 全局名与值；调用日志仅明确展示 `days`，持续时间块的 `years` 由 CWTools duration 定义辅助支持。 | 保留原版设计 `years = 5`，避免自行换算闰年。需要原生计时和存档重载验证。待确认锁没有自动到期。 |
| Scope links，1.15.2 event_targets.log | `country_definition` Country → Definition、`civil_war_origin_country` Country → Country、`state` POP → State、`owner` POP/State → Country、`culture` POP → Culture，以及 `s:`、`cu:`、`cd:`、`scope:`、`var:`、`global_var:`。 | 保留 CHI、内战来源与中央政府三支。中央政府是原版脚本的变量名称，生成文档不能证明新版仍写入该名称。 |
| 式值与脚本参数，1.15 类型文档 | `min` 下限、`max` 上限、`floor = yes`。运算逐项求值。 | 读取预计算矩阵额度并上下限截取，独立检查边界。RC2 由生成器写出固定文化和地区调用，配对过程不使用运行时脚本参数。停止标记由文档化的 `set_variable = name` / `has_variable = name` / `remove_variable = name` 管理。 |
| Journal 和 Button，1.15 类型文档，1.15.2 conclude_journal_entry 增量 | Country context，`scripted_button` 指向按钮；零个 outcome 合法。Button 的 `visible`、`possible`、`effect`、`ai_chance = { base = 0 }` 有原生模板。 | 复用现有原版 group，明确 context、采用 country context 的 pin 字段。省略 outcome 与 timeout。执行入口再次核对资格、冷却和锁。 |
| `trigger_event` / `custom_tooltip` / `hidden_effect`，1.15.2 effects.log；数据类型日志 | 事件可延迟 `days = 1`。可显示 Tooltip 并隐藏调度脚本。类型中有 `Scope.Var`、`ScriptValue`、`GetValue`、`TopScope.sState`。 | 正式操作三类结果。隔日事件仅用于独立探针，避免把隔日的自然变化结为迁移。游戏内验证弹窗的变量显示和事件作用域。 |

公开资料不能确定跨国/海外/未整合的原生限制、文化与宗教合并策略、完全搬空后的引用失效规则，以及触发后的州总人口何时刷新。脚本通过实际州定位和保守校验处理这些不确定性。原生示例来自日志与类型模板，未找到 1.15.2 原版战役中使用此效果的实例。

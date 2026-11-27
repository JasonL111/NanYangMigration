# 1.15.2 原生技术依据

本次重新同步了 Modding Co-op 的版本库，最新可取得的 1.15 正式补丁文档为 **1.15.2**。Steam 公告、Paradox 论坛与 Victoria 3 Wiki 在本环境返回 403，官方公告无法独立核对。实现使用 1.15.2 的公司类型说明、引擎生成日志，以及公开项目从该版本游戏提取的结构化原版数据。该快照的版本来源为 `launcher-settings.json`。 [1.15.2 Release Digest](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/tree/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2) · [1.15.2 原版快照 manifest](https://github.com/jakeOmega/Vic3TimelineExtended/blob/2710a77703e2e3c982d4b29425bd1e34fb496835/vanilla_parsed/manifest.json)

| 接口 | 作用域和用途 |
| --- | --- |
| `potential`、`attainable`、`possible` | 1.15.2 将隐藏、潜在、可达和可成立区分为 Country 条件。分别配置国家资格、科技与已建工业规模。 |
| `can_establish_in` | 1.15.2 公司类型说明将此字段定义为 State 条件，限制公司建筑可选州。鲁农用 `state_region = s:STATE_SHANDONG`。同一州触发器用于国家侧 `any_scope_state` 的 20 级统计。目标版州历史快照中山东由 `CHI` 持有。 |
| `building_types` | 使用直接基础清单。原版额外行业特许才使用 `extension_building_types`。 |
| `ai_will_do = { always = yes }` | 1.15.2 类型说明允许这种写法。这里无额外 AI 施工目标，原版仅在能立即成立时把该公司纳入选择。 |
| `every_scope_building`、`level` | 原生遍历支持 Country 和 State，循环内为 Building；Scope Link `level` 输出建筑等级。Script Value 的列表求和只加实际符合经营清单的建筑。单建筑门槛使用 Country 原生 `country_has_building_type_levels` 与 `bt:` 参数。 |
| `country_definition`、`civil_war_origin_country`、`global_var:` | 1.15.2 的 Country 链接支持国定义和内战来源。只在变量存在时查询其 Country。1.15.2 原版 `je_reunify_china` 的 outcome 仍读取 `chinese_central_government`，用于原版中央政府识别。 |

[1.15.2 Company Type 文档](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/types/companies.md) · [Effects](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/effects.log) · [Triggers](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/triggers.log) · [Scope Links](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/event_targets.log) · [Script Value 类型说明](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/documentation/types/script_values.md)

## 基础经营的数量

1.15.2 公司类型说明的 `building_types` 按列表读取，文档未标注上限。CWTools 的类型规则基数为 `1..inf`，当前标注 1.15.2 的 Vic3TimelineExtended 中可找到拥有九项基础建筑的定义。目标版原版快照里的实际公司最多列三项。现有证据支持直接声明全部经营建筑，无法据此确认引擎或面板实际显示十项。中华实业保留华兴七项、鲁农六项、丰殖十项和矿业六项，列入实机验收。 [CWTools company_types](https://github.com/cwtools/cwtools-vic3-config/blob/bec10017635de6dac01525210b4c932db0ce1c40/config/common/company_types.cwt) · [1.15.2 社区公司定义](https://github.com/jakeOmega/Vic3TimelineExtended/blob/2710a77703e2e3c982d4b29425bd1e34fb496835/common/company_types/extra_companies_flavored.txt) · [原版公司快照](https://github.com/jakeOmega/Vic3TimelineExtended/blob/2710a77703e2e3c982d4b29425bd1e34fb496835/vanilla_parsed/common/company_types.json)

## 繁荣、生产与图形

- `prosperity_modifier` 在引擎判定公司繁荣时生效。1.15.2 原版 `company_basic_steel` 使用 `state_construction_mult`，同版引擎日志将它定义为州每周建造进度的效率调整。`building_university_throughput_add` 的 Mask 为 Building，专门修正大学投入产出。`state_standard_of_living_add` 的 Mask 为 State，描述为在 Wealth 基础上的固定生活水平加值。1.15 的 Modifier 类型文档说明国家来源的州／建筑修正可沿其修正图传递。本项目通过公司的国家繁荣收益设置这些键。 [原生 Modifier 注册表](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.2/docs/modifiers.log) · [修正图说明](https://github.com/Victoria-3-Modding-Co-op/Modding-Digests/blob/0e94618d6a1b1599d4c78cc074282598de4d59b2/1.15.0/types/modifier_type_definitions.md)
- 1.15.2 快照确认独立汽车工业与发动机厂，汽车 PM 需要 `combustion_engine`，飞机 PM 需要 `military_aviation`。快照也确认铜矿、葡萄园、砂金场所有制、五种商品粮农场和香蕉。通过建筑 → PM 组 → PM 的正数基础商品产出，核对了八个品牌均有对应生产建筑。 [1.15.2 建筑数据](https://github.com/jakeOmega/Vic3TimelineExtended/blob/2710a77703e2e3c982d4b29425bd1e34fb496835/vanilla_parsed/common/buildings.json) · [生产方式数据](https://github.com/jakeOmega/Vic3TimelineExtended/blob/2710a77703e2e3c982d4b29425bd1e34fb496835/vanilla_parsed/common/pms.json)
- 原版福特汽车、阿萨姆茶、爱立信设备等品牌通过 `base_good`、`texture` 与 `possible = { has_dlc_feature = mp1_content }` 定义。此处将 DLC 检查放在品牌自身，并用 Company Scope 上的 `company_is_prosperous` 约束品牌生产。公司成立走独立的 Country 条件。煤炭有可生产的原生基础商品，原版快照没有对应品牌实例，其首次实际生产是验收重点。发电厂的电力为 `local = yes`，华光采用原版电气工业可生产、有原版品牌实例的电话机。 [1.15.2 原版品牌快照](https://github.com/jakeOmega/Vic3TimelineExtended/blob/2710a77703e2e3c982d4b29425bd1e34fb496835/vanilla_parsed/common/prestige_goods.json) · [商品定义](https://github.com/jakeOmega/Vic3TimelineExtended/blob/2710a77703e2e3c982d4b29425bd1e34fb496835/vanilla_parsed/common/goods.json)
- 公司直接以 `icon = "gfx/interface/icons/company_icons/cie_*.dds"` 读取纹理，品牌的 `texture` 复用相应商标。1.15.2 社区参考使用透明 256×256 的 BC7。中华实业选择等比置中于 256×256 透明画布的 BC3/DXT5，经 ImageMagick 验证可解码且边缘含 Alpha。256×256 与压缩选型是资源规格，真实引擎渲染需验收。公司背景使用已在 1.15.2 原版快照出现的游戏纹理引用。 [1.15.2 社区公司图标规格](https://github.com/jakeOmega/Vic3TimelineExtended/blob/2710a77703e2e3c982d4b29425bd1e34fb496835/scripts/image_pipeline/convert_company_icon.py) · [CWTools Prestige Good 类型](https://github.com/cwtools/cwtools-vic3-config/blob/bec10017635de6dac01525210b4c932db0ce1c40/config/common/prestige_goods.cwt)

审计工具可重读上述固定提交对应的 `vanilla_parsed` 目录及 Modding Digests，原版数据没有纳入安装包。

```sh
python3 dev/chinese_industrial_enterprises/tools/audit_native.py /path/to/vanilla_parsed /path/to/Modding-Digests
```

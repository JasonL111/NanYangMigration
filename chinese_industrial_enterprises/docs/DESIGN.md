# 设计与实际建筑映射

八家企业均为架空设定。成立走原版公司界面，科技门槛放在 `attainable`，完成建筑规模放在 `possible`。综合企业按合计等级计算，只要组合达标即可。用于成立的科技和规模采用任务建议值，公司槽、行业投资、外国投资和繁荣状态由原版控制。

## 建筑与繁荣奖励

| 公司 | 原生建筑映射 | 原生修正 |
| --- | --- | --- |
| 华兴实业 | `building_automotive_industry`、`building_tooling_workshop`、`building_steel_mill`、`building_motor_industry`、`building_railway`、`building_power_plant` | `state_construction_mult = 0.10`、`building_university_throughput_add = 0.10` |
| 鲁农集团 | `building_wheat_farm`、`building_rice_farm`、`building_rye_farm`、`building_maize_farm`、`building_millet_farm`、`building_banana_plantation` | `state_standard_of_living_add = 1` |
| 丰殖商号 | `building_tea_plantation`、`building_coffee_plantation`、`building_cotton_plantation`、`building_silk_plantation`、`building_dye_plantation`、`building_sugar_plantation`、`building_tobacco_plantation`、`building_opium_plantation`、`building_rubber_plantation`、`building_vineyard` | 各用对应的 `building_<名称>_throughput_add = 0.20` |
| 中华矿业总公司 | `building_coal_mine`、`building_iron_mine`、`building_copper_mine`、`building_lead_mine`、`building_sulfur_mine`、`building_gold_mine` | 各用对应的 `building_<名称>_throughput_add = 0.15` |
| 中华石油公司 | `building_oil_rig` | `building_oil_rig_throughput_add = 0.20` |
| 华光电气公司 | `building_power_plant`、`building_electrics_industry` | `building_power_plant_throughput_add = 0.15` |
| 神州汽车制造公司 | `building_automotive_industry`、`building_motor_industry` | `building_automotive_industry_throughput_add = 0.20`、`building_motor_industry_throughput_add = 0.20` |
| 凌云航空制造公司 | `building_automotive_industry` | `building_automotive_industry_throughput_add = 0.20` |

国家级繁荣收益覆盖相应州和建筑。华兴大学吞吐量走独立建筑键，大学只享受收益。鲁农的固定生活水平加值适用于各阶层，山东限制仅用于总部和成立规模。原版农场的果品副产出和香蕉均属鲁农经营范围。丰殖逐建筑配值，因此葡萄园有加成，香蕉和粮食农场保持各自的原生吞吐量。

原版 `building_gold_mine` 允许一般所有权，自动生成的砂金场 `building_gold_field` 设有 `can_switch_owner = no`。矿业清单采用六种归入 `bg_mining` 的矿山。石油经营使用独立的 `building_oil_rig`。

## 车辆、航空与电气

`building_motor_industry` 生产发动机，`building_automotive_industry` 的 `pm_automobile_production` 生产汽车，`pm_aeroplane_production` 将其中一部分产能改为飞机。凌云使用飞机所在的原生建筑，原版快照中没有独立航空发动机产品和工厂。厂级吞吐量会作用于该建筑启用的其他生产方式，包括共用的汽车、飞机及坦克产出。

华光在发电厂之外经营原版电气工业，发电厂达到 15 级才可成立。电力为本地商品，品牌选用有原版品牌先例的电话机。要生产「华光电气设备」，公司需要实际拥有相应电气工业产出。八个品牌均按原生基础商品衍生，`prestige_bonus = 0.1` 沿用原版品牌示例。

## 原生执行范围

除鲁农外的七家由原版挑选总部。多产业门槛在评估时仅汇总当前国家或州中的相关建筑等级，专业企业用引擎的单类型全国建筑级别检查。公司定义中的 AI 条件等于开放原版选择。正式包只包含定义、计算门槛的值、两种触发器、文本和商标。测试用大清开局辅助文件在 `dev/`。

# 下南洋 · Nanyang Migration 1.0.1

目标版本：**Victoria 3 1.13.11 (Matcha)**。原生 Paradox Script，运行时无外部依赖。
这是已生成并通过静态/模拟执行检查的安装候选包；本环境没有游戏，
**尚未验证引擎加载、真实 POP 数量、保存重载与计时行为，不能声称游戏内验收已通过**。

## 安装与启用

1. 解压 `nanyang_migration.zip`。保留根目录名 `nanyang_migration`，包括隐藏的
   `.metadata/metadata.json`；不要把两个同名文件夹套在一起。
2. 将该文件夹放到用户数据目录的 `Victoria 3/mod/` 中：
   - Windows：通常为 `文档/Paradox Interactive/Victoria 3/mod/`；文档可能被 OneDrive 重定向。
   - Linux：通常为 `~/.local/share/Paradox Interactive/Victoria 3/mod/`。
   - macOS：通常为 `~/Documents/Paradox Interactive/Victoria 3/mod/`。
3. 启动 Launcher，在“所有已安装的 Mod / All installed mods”中重新加载，
   将“下南洋 · Nanyang Migration”加入当前播放集并启用。只有元数据与游戏脚本
   应位于同一 Mod 根目录；Victoria 3 使用 `.metadata/metadata.json`，不依赖旧式 `.mod` 绝对路径。
4. 如果所用 Launcher 没有自动列出手动放入的本地 Mod，使用其
   “Mod 工具 / Mod tools → 创建 Mod / Create mod”，选择 Victoria 3，名称填写“下南洋”，
   目录填写 `nanyang_migration`。先备份本包，然后将本包 `common/`、`events/`、
   `localization/`、`docs/`、`README.md` 复制进该工具创建的本地 Mod 根目录，
   保留 Launcher 生成的注册元数据。重新加载并加入播放集。
   Launcher 的语言与具体按钮名称可能随独立版本变化；此备用注册路径未在当前环境实测。
5. 不要把文件复制到 Steam 的游戏安装目录。本包无需任何 DLC、科技、建筑或法律。

## 使用

1836 年以大清开始，查看日志中的长期条目“下南洋”，点击“组织下南洋”。
条目不会自动完成或失败。新激活条目取决于游戏正常的日志评估周期。
按钮仅对玩家开放，AI 权重为零。暂停时执行同步迁移逻辑，不等待普通移民吸引力。
无需市场连接、外交协议或目的地所有权。

国家判断使用 `country_definition = cd:CHI`，所以大清、共和国、人民共和国的动态名称
不会影响资格；也支持 CHI 内战来源国及原版 `chinese_central_government` 指向的中国中央政府。
不以汉文化主流为唯一条件，因此不会把所有华人小国都当作中国。自定义整合包使用其他国家
定义且不设置这些原版关系时不会自动获得资格。

日志显示累计成功次数、当前计划、上次目标、上次实际完成量以及本次成功后的下一次目标。
按钮条件显示冷却是否满足；不添加自定义 GUI，也不声称显示未经验证的冷却结束日期。
点击后弹出成功或零迁移结果通知。零迁移时按钮可继续尝试，但不消耗冷却或成功次数。

## 精确设计参数

所有百分比均以本次理论总目标为分母，不是每种文化各自按目的地比例分配。

| 目的地 | 闽 min | 粤 yue | 客家 hakka | 汉 han | 合计 |
|---|---:|---:|---:|---:|---:|
| 马来亚及新加坡 | 12% | 10% | 7% | 6% | 35% |
| 荷属东印度 | 13% | 4% | 6% | 2% | 25% |
| 暹罗 | 14% | 3% | 1% | 2% | 20% |
| 印度支那 | 2% | 9% | 1% | 0% | 12% |
| 菲律宾 | 4% | 1% | 0% | 0% | 5% |
| 缅甸 | 0% | 3% | 0% | 0% | 3% |
| 合计 | 45% | 30% | 15% | 10% | 100% |

第 n 次成功发动的目标为 `min(round(2000000 × 1.25^(n−1)), 5000000)`，
采用正数四舍五入：2,000,000 → 2,500,000 → 3,125,000 → 3,906,250 →
4,882,813 → 5,000,000，后续保持不变。脚本使用该有限序列，避免固定小数迭代误差。

每个非零矩阵格先向下取整，再以“最大余数法”补足总额，余数相同时按上表行顺序、
文化列顺序处理。理论总额始终等于目标，各格与理想份额差小于1人；整数人口不可能在
所有目标值下同时满足完全精确的百分比。每格内部，按当前实际存在的 State 等额分配，
逐个以剩余额度除以剩余州数向下取整，余数落到后续州，不设新加坡、爪哇等子权重。

## 来源、真实迁移及异常

所有拥有的州都能供给人口，包括非传统聚居州、未整合州、海外州；没有中国省份白名单。
来源为点击时的四文化 POP 快照，每个对象的可抽取额度不超过其初始总人口。
迁入后新产生的 POP 不加入来源快照；合并进既有来源 POP 的迁入者不会扩大该对象额度。
整个对象被搬离后，其来源州不再匹配，不能再次作为原来源使用。
本机制在原生 POP 对象可用的粒度上追踪额度，不能追踪合并后每个个人的身份。

仅调用原生 `move_partial_pop = { state = … population = … }`，
不会创建 POP、杀死人口、添加增长修正、改变文化或宗教。
从 `total_size` 读取来源额度，不将 workforce 误作总人口。
原生规则会让迁入者失业，或使不能失业/不允许的奴隶职业转为默认职业。

实际量以每笔转移前后的目标州 `state_population` 差额记录，不将请求人数直接充当完成量。
只有实际量大于零才增加成功次数并设置 `years = 5` 的持久化冷却变量。
请求值为整数；**`population` 在 1.13.11 中的总人口/劳动力单位、引擎拆分取整和
州统计是否同步刷新仍需游戏实测**。公开生成文档说明支持该参数，未给出足够证据验证
这些实现细节，因此自动测试中的精确人数不构成真实引擎的精度保证。

来源不足时减量，不跨文化补足；目的区域无有效拥有者时整格跳过，不跨地区改派。
来源和目的为同一实际州时跳过；某目的州无法从其他来源补齐时保留缺额。
异常条件下矩阵描述的是理论额度，实际比例可以偏离。
如果目标州也属于中国，人口是国内州际迁移，中国全国总量不会因此下降，
但来源州减少与目标州增加必须守恒。

为避免改换国家/革命后重置，本 Mod 的 `nym_uses`、`nym_cooldown`、最近成功记录
使用整局存档级全局变量，所有符合资格的中国继承国共享。同一局多人同时操作不同中国
继承国也共享次数和冷却，不是每玩家一套。失败不覆盖上次成功总记录；
`nym_actual_<区域>_<文化>` 是最近一次尝试的逐格实际记录，失败尝试可将其更新为0。

## 地理映射（1.13.11 公开数据核对）

完整 ID 保存在 `docs/design.json` 和 `common/scripted_triggers/nanyang_triggers.txt`。

- 马来亚及新加坡：MALAYA，包含该 Region 内所有实际分割州，非独立 Singapore ID。
- 荷属东印度：ACEH、NORTH_SUMATRA、SOUTH_SUMATRA、WEST_JAVA、CENTRAL_JAVA、EAST_JAVA、
  WEST_BORNEO、EAST_BORNEO、CELEBES、MOLUCCAS、SUNDA_ISLANDS、WESTERN_NEW_GUINEA。
  不把历史上英属的 NORTH_BORNEO 或东新几内亚纳入荷属东印度。
- 暹罗：BANGKOK、CHIANG_MAI、NAKHON_RATCHASIMA。
- 印度支那：TONKIN、ANNAM、MEKONG、CAMBODIA、LAOS。
- 菲律宾：LUZON、VISAYAS、MINDANAO。
- 缅甸：ARAKAN、PEGU、MANDALAY、KACHIN、SHAN_STATES、TENASSERIM。

上述均带 `STATE_` 前缀。地图边界采用游戏 State Region 的粒度，不按1836年国家所有者
筛选。被其他国家占有、地区独立或国家 Tag 消失均不改变接收资格。

## 验证与兼容性

详见 `docs/VALIDATION.md`：已做文件、引用、本地化、目标曲线、整数分配及实际脚本
在合成人口模型中的执行测试。未在游戏中加载，未验证真实文化人数、宗教保留、
职业转换、国家继承、原生冷却计时、真实存档重载、统计刷新、Launcher 注册或错误日志。
不宣称“安装后已经保证可运行”。首次请使用独立测试存档与单独播放集。

不覆盖任何原版定义，所有自定义 ID 使用 `nym_`/`nanyang_migration` 命名空间。
修改地图、文化、国家定义、日志系统或人口效果的 Mod 需要重新核对兼容性。
脚本集合会改变校验和；不要假定兼容成就或多人未统一的 Mod 播放集。

## 游戏内验收步骤

启用 `-debug_mode` 后建立1836年大清新档，待日志激活，在暂停状态下记录四文化来源总人口
及各目标州人口，点击一次，核对迁出/迁入、逐格统计、总目标2,000,000和实际完成量。
检查用户数据 `logs/error.log` 中本次加载产生的 `nanyang`/`nym_`/脚本报错。
再做立即二次点击、保存退出重载、经过5个游戏年后的二次点击，检查2,500,000目标。
在测试档备份后，用调试控制台 `effect remove_global_variable = nym_cooldown` 仅移除
冷却，可依次核对第3至第7次目标；此命令不是正常玩法的一部分。
还需测试缺文化、缺目标州、分割州、革命继承、同国目标、人口单位及原生拆分/合并精度。
任何效果要求精度或 scope 报错，均应以真实错误日志和前后 POP 数据修正，不能以模型通过代替。

## English installation summary

Extract the complete `nanyang_migration` folder into your Victoria 3 user-data `mod` directory,
preserving `.metadata/metadata.json`. Reload local mods in the Launcher, add it to a playset and
enable it. If local discovery is unavailable, register a local mod through the Launcher's Mod tools,
then copy the content folders into that mod and retain its generated registration metadata.
Start as China and use the permanent Journal button. English and Simplified Chinese are provided.
Target: 1.13.11; native-engine loading and gameplay have **not** been tested in this cloud environment.

## 1.0.1 更新须知

修复原生Script Value的min/max上下界反用，包含迁入统计归零与抽取量超限两处。
1.0.0显示失败也可能已经迁移了人口，请优先载入点击之前的存档。
完全退出游戏后删除旧Mod目录，再解压新版覆盖安装，避免两个版本同时启用。
本版经24项静态/模拟测试，尚无游戏内实测。

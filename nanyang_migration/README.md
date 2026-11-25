# 下南洋 · Nanyang Migration 1.1.0 RC1

目标版本：**Victoria 3 1.15.2**。原生 Paradox Script，运行时无外部依赖。
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
按钮仅对玩家开放，AI 权重为零。点击时调用原生直接迁移。即时读数能否在暂停中完整更新，请查阅诊断步骤。
无需市场连接、外交协议或目的地所有权。

国家判断使用 `country_definition = cd:CHI`，所以大清、共和国、人民共和国的动态名称
不会影响资格；也支持 CHI 内战来源国及原版 `chinese_central_government` 指向的中国中央政府。
不以汉文化主流为唯一条件，因此不会把所有华人小国都当作中国。自定义整合包使用其他国家
定义且不设置这些原版关系时不会自动获得资格。

日志显示累计成功次数、当前计划、上次目标、上次实际完成量以及本次成功后的下一次目标。
按钮条件显示冷却是否满足；不添加自定义 GUI，也不声称显示未经验证的冷却结束日期。
结果分为已确认成功、未调用转移、待确认。未发出转移请求时可重试。调用后结果仍待确认时，存档会保留操作锁。

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

每笔请求限制为当时 POP 大小、点击时剩余来源预算、目的州额度中的最小值。发出请求前
扣减来源快照预算，避免合并扩充额度。完成后分别重扫两个州该文化的 POP，来源减少量和
目的增加量必须为相同的正数，且不超过请求量，才计入实际总量。若原生效果少移且两端读数
一致，按实测值结算。出处不足时，已发出的请求占用来源预算，即使引擎只执行了一部分，
因此极端拆分情况下可更保守地少移一部分。

任何一笔无法核对时，中止余下调用，保留全局 `nym_pending`。这需要加载点击前的
存档才能重新尝试。等待游戏日推进不会自动认定到账或解除锁定，因为正常人口变化
也会改变读数。确认整批成功后增加一次成功次数，启动 `years = 5` 冷却，更新记录。
全程没有发出请求的批次不更新成功记录或冷却。

公开原生文档确认 `move_partial_pop` 的 POP 作用域与三种写法。1.15.2 下 `population`
是否含家属、即时 POP 读数、跨国限制、完整拆分/合并细节留给独立小额诊断验证。
若引擎按照与原计划不同的单位移动，脚本能拦截后续操作，已发生的第一笔原生调动没有回滚接口。

来源不足时减量，不跨文化补足；目的区域无有效拥有者时整格跳过，不跨地区改派。
来源和目的为同一实际州时跳过；某目的州无法从其他来源补齐时保留缺额。
异常条件下矩阵描述的是理论额度，实际比例可以偏离。
如果目标州也属于中国，人口是国内州际迁移，中国全国总量不会因此下降，
但来源州减少与目标州增加必须守恒。

为避免改换国家/革命后重置，本 Mod 的 `nym_uses`、`nym_cooldown`、最近成功记录
使用整局存档级全局变量，所有符合资格的中国继承国共享。同一局多人同时操作不同中国
继承国也共享次数和冷却，不是每玩家一套。失败不覆盖上次成功总记录；
`nym_actual_<区域>_<文化>` 是最近一次尝试的逐格实际记录，失败尝试可将其更新为0。

## 地理映射（保留设计 ID）

完整 ID 保存在 `docs/design.json` 和生成的 `common/scripted_effects/nanyang_effects.txt`。公开 1.15 差异未列出这些 ID 的改名，但目标地图文件在 1.15.1 有修改，新版原始数据的逐项验证仍待执行。

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

## 升级与游戏内验收

1. 完全退出游戏，移除旧 Mod 目录再解压新版，确保播放集中只启用一个正式版本。
2. 用 1.15.2 新建 1836 大清备份测试档。打开“下南洋”，检查按钮和 200 万计划。先做独立小额诊断可确认原生迁移行为，见仓库的诊断 ZIP。
3. 在测试档点击一次正式按钮，核对结果、弹窗中的末笔请求及两端人口差额，并比较来源和目的州的文化人口。核对累计成功为 1、下次目标为 250 万、五年冷却和保存重载。
4. 若显示“迁移待确认”，保留操作前存档和完整弹窗。一次性提供游戏版本/校验码、Mod 版本、弹窗、同次运行的 `logs/error.log` 和独立诊断报告。必要时提供点击前后的人口界面截图。

旧游戏版本存档升级取决于游戏自身兼容性，本候选版未实测。旧 Mod 的 `nym_uses`、`nym_cooldown`、最近成功记录继续读取，旧暂存数据不参与新操作。1.0.0–1.0.2 的零记录可能对应已发生的移动。优先以旧版第一次点击之前的备份验证。由于没有可靠的旧迁移账目，此版本不能自动恢复旧版人口。

开发与校验命令见仓库根目录 [README](../README.md)。已知缺陷、限制及版本差异见 [兼容性调查](docs/COMPATIBILITY_1_15.md) 与 [验证报告](docs/VALIDATION.md)。

## English installation summary

Target: Victoria 3 1.15.2, release candidate 1.1.0 RC1. Extract the complete `nanyang_migration` folder into the game's user-data `mod` directory, keeping `.metadata/metadata.json`. Enable it in a Launcher playset. No DLC or runtime dependencies are required. Use a backed-up new Qing save. If the report says “Transfer Unconfirmed”, reload the pre-attempt save for another test and retain the report and game log. Engine acceptance remains pending.

# 下南洋 · Nanyang Migration 1.1.3

目标版本：**Victoria 3 1.15.2**。原生 Paradox Script，运行时无外部依赖。
首航计划 **200,000 人**，成功后下一航次增加 **25%**，单次最多 **500,000 人**，
每次成功后休整 **3 个游戏年**。

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
   `localization/`、`gfx/`、`docs/`、`README.md` 复制进该工具创建的本地 Mod 根目录，
   保留 Launcher 生成的注册元数据。重新加载并加入播放集。
   Launcher 的语言与具体按钮名称可能随独立版本变化；此备用注册路径未在当前环境实测。
5. 不要把文件复制到 Steam 的游戏安装目录。本包无需任何 DLC、科技、建筑或法律。

## 使用

1836 年以大清开始，查看日志中的长期条目“下南洋”，点击“组织下南洋”。
条目不会自动完成或失败。新激活条目取决于游戏正常的日志评估周期。
按钮仅对玩家开放。点击后将应募人家送往南洋。
无需市场连接、外交协议或目的地所有权。

国家判断使用 `country_definition = cd:CHI`，所以大清、共和国、人民共和国的动态名称
不会影响资格；也支持 CHI 内战来源国及原版 `chinese_central_government` 指向的中国中央政府。
不以汉文化主流为唯一条件，因此不会把所有华人小国都当作中国。自定义整合包使用其他国家
定义且不设置这些原版关系时不会自动获得资格。

日志显示累计成功次数、当前计划、上次目标、上次实际完成量以及本次成功后的下一次目标。
按钮条件显示冷却是否满足；不添加自定义 GUI，也不声称显示未经验证的冷却结束日期。
三个航程结果弹窗均使用为本 Mod 绘制的原创南洋港口插图。航报显示实际抵达人数和下一航次计划。航程未能启行时可再次筹办。若结果是「航报未至」，请载入启航前的存档再试。

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

第 n 次成功发动的目标为 `min(round(200000 × 1.25^(n−1)), 500000)`，
采用正数四舍五入：200,000 → 250,000 → 312,500 → 390,625 →
488,281 → 500,000，后续保持不变。脚本使用该有限序列，避免固定小数迭代误差。

每个非零矩阵格先向下取整，再以“最大余数法”补足总额，余数相同时按上表行顺序、
文化列顺序处理。理论总额始终等于目标，各格与理想份额差小于1人；整数人口不可能在
所有目标值下同时满足完全精确的百分比。每格内部，按当前实际存在的 State 等额分配，
逐个以剩余额度除以剩余州数向下取整，余数落到后续州，不设新加坡、爪哇等子权重。

## 来源、真实迁移及异常

所有拥有的州都能供给人口，包括非传统聚居州、未整合州、海外州；没有中国省份白名单。
开航时统计四种文化的来源规模。每笔使用来源州当前可用的实际 POP。一个州收到本次迁入的
某种文化后，当次暂停从该州迁出该文化，避免把刚抵达的人再次移走。这个保护也会保留该州
尚未迁出的原有人口，可能减少国内路线的完成量。其他文化仍可迁出，下次起航可重新选择。

仅调用原生 `move_partial_pop = { state = … population = … }`，
不会创建 POP、杀死人口、添加增长修正、改变文化或宗教。
从 `total_size` 读取来源额度，不将 workforce 误作总人口。
原生规则会让迁入者失业，或使不能失业/不允许的奴隶职业转为默认职业。

每笔请求受当时 POP 大小和目的州额度限制。接收标记写在目标州，并在调用原生迁移前
回读确认。完成后分别重扫两个州该文化的 POP。来源减少量和目的增加量须为相同的正数，
且不超过请求量，才计入实际总量。若原生效果少移且两端读数一致，按实测值结算。

任何一笔无法核对时，中止余下调用，保留全局 `nym_pending`。这需要加载点击前的
存档才能重新尝试。等待游戏日推进不会自动认定到账或解除锁定，因为正常人口变化
也会改变读数。确认整批成功后增加一次成功次数，启动 `years = 3` 冷却，更新记录。
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

玩家已确认 RC4 的迁移流程可在游戏中正常运行。1.1.0 的文案、新额度和三年冷却已通过
自动化验证。验证范围见 [验证报告](docs/VALIDATION.md)。

不覆盖任何原版定义，所有自定义 ID 使用 `nym_`/`nanyang_migration` 命名空间。
修改地图、文化、国家定义、日志系统或人口效果的 Mod 需要重新核对兼容性。
脚本集合会改变校验和；不要假定兼容成就或多人未统一的 Mod 播放集。

## 从旧版升级

退出游戏后，用新版目录替换旧安装，并在启动器中确认版本为 **1.1.3**。
存档中的成功次数和历史航次保留。**下一次计划按新额度计算**。若旧版已开始冷却，
原来的到期时间保留，升级后成功的航次起用三年冷却。

开发与校验命令见仓库根目录 [README](../README.md)。已知缺陷、限制及版本差异见 [兼容性调查](docs/COMPATIBILITY_1_15.md) 与 [验证报告](docs/VALIDATION.md)。

## English installation summary

Target game is Victoria 3 1.15.2. Extract the `nanyang_migration` folder from the 1.1.3 ZIP into the
game's user-data `mod` directory, keeping `.metadata/metadata.json`, then enable it in the Launcher.
The first expedition plans for 200,000 people. Each success raises the next plan by 25% to a maximum
of 500,000 and starts a three-year cooldown. Existing saves retain completed expeditions and cooldowns
already in progress.

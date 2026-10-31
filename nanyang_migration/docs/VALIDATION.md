# 验证报告

目标：Victoria 3 **1.13.11 (Matcha)**；Mod：**1.0.0**。

## 环境与资料

实际检查了工作区及 `/opt`、`/home` 下的可用安装，没有找到 Victoria 3。
工作仓库原为空，无原版游戏可启动，也没有已有测试存档。没有修改游戏本体。

使用以下公开资料，未把原版游戏数据复制进 Mod：

1. [alcaras/v3ref](https://github.com/alcaras/v3ref)，提交
   `bd8e3f7da313a57d0509559d59cff7617cc49513`。
   `data/patch.json` 明确标注 `1.13.11 (Matcha)`，同步时间 `2026-08-25T12:00:00`。
   用其生成的 `src/data/cultures.json`、`countries.json`、`states.json`、
   `journal_entries.json` 核对四文化、CHI、所有目的地 State Region 和外事日志组。
   这是有版本标记的社区数据快照，不是本机游戏文件或官方认证。
   相关输入的 SHA256 和实际使用的 ID 子集保存在 `reference_ids.json`。
2. [cwtools/cwtools-vic3-config](https://github.com/cwtools/cwtools-vic3-config)，提交
   `ba728e59a22e18dd590964e1c0201976852f46a8`（2026-06-22）。
   查阅 `config/effects.cwt`、`triggers.cwt`、`links.cwt`、`lists.cwt`、
   `formula.cwt`、`list_effects.cwt` 及 Journal、Scripted Button、Script Value、Event 定义。
   同时查阅其 `script-docs/effects.log`、`triggers.log` 与数据类型日志。
   原生 `move_partial_pop` 支持 pop scope、state、population、population_ratio；
   `total_size` 是 pop 总大小，`state_population` 是州人口；变量可在 pop scope 使用；
   `set_global_variable` 的持续时间块支持 `years`。
   其提交未标明完整对应1.13.11，因此只能报告接口资料核对，不能称为目标版本引擎编译通过。
3. [tjysdsg/Victoria-3-files](https://github.com/tjysdsg/Victoria-3-files)，提交
   `0e8b62590c36bc9fdd2c8cba3cb5dda255092656`（2025-06-23）。
   阅读实际 Journal/Scripted Button 示例、CHI 动态国名、文化定义和旧版地图脚本，
   验证 `.metadata` 替代旧式描述符的社区规范、本地化形式及原版中国中央政府关系用法。
   旧版地图不是1.13.11地图验证依据；目的地以第1项为准，已补上旧地图没有的暹罗新州。
4. 尝试访问 Paradox Wiki Effect 页，返回 HTTP 403，未使用不可读取的页面作验证证据。

## 已执行的检查

命令：`python3 -m unittest discover -s tests -v`。

**23项测试通过，0失败、0跳过**，详细当前运行输出见 `test-results.txt`。
`tools/script_harness.py` 会解析并执行实际生成的脚本子集，未知命令报错，
不是单独复制迁移算法后只测试副本。

覆盖：

- 所有运行文件非空、无空目录；JSON、脚本块结构和比较表达式解析。
- 日志→按钮→效果→事件引用，参数化脚本引用，中英本地化键一致及 UTF-8 BOM。
- 1.13.11版本标记文化/州ID，地理集合互不重叠。
- 矩阵行列和，前6次完整迁移目标，第7至第20次上限，最大余数整数分配。
- 由实际生成脚本执行前6次迁移，在合成人口模型中校验总人口守恒、逐格人数与来源减少。
- 同一 State Region 的3个实际分割州：各格份额差至多1人。
- 地区缺失、文化缺失、人口不足、零迁移不扣次数/冷却。
- 目标所有者改变、来源位于阿拉斯加而非中国传统省份、AI不可操作。
- 同国目的州、同州排除、预存来源对象合并后的额度限制和宗教字段保留。
- 保存标量状态后的继承国冷却拦截、模拟原生变量到期后的第二次目标。
- 最近一次成功记录不被失败覆盖；永久日志；冷却脚本使用5年而非硬编码1825天。

**模拟层的边界**：Harness 中的原生人口移动是开发者定义的模型，按“population代表总人数、
州人口立即刷新、合并保留文化宗教”执行。故通过测试只能验证脚本控制流与账目算法在这些
前提下正确，不能证明引擎实现满足这些前提。原生年份到期、游戏序列化、对象销毁语义、
POP拆分精度、实际宗教/职业行为均未通过该模型验证。

## 未执行，仍需真实游戏验收

- Launcher 识别/注册与1.13.11加载，无真实引擎语法检查和 scope 错误日志。
- 1836大清日志出现、暂停点击、目标地区实际文化人数与迁出/迁入相等。
- `population` 参数数值单位是否包含 dependents，`total_size` 与其对应关系。
- 原生整数/固定小数取整、POP拆分合并、死亡对象列表迭代、州人口缓存的即时性。
- 保存退出重载、5个原生游戏年的到期、革命胜利/新中央政府继承。
- 缺文化、分割州、所有权变更和同国迁移的真实游戏边界场景。
- UI动态值、结果弹窗、英文与简体中文显示。

安装包包含完整脚本和说明，没有在这些项目未测试时声称“游戏已跑通”。
README列有具体的游戏内验收步骤。当前无进一步可运行的游戏内验证工具。

## 包与可重复性

运行 `python3 tools/build_mod.py` 可重建脚本和本地化。
运行 `python3 tools/package_mod.py` 会重跑测试并重建ZIP，检测每个文件、CRC和SHA256。
游戏不依赖这两项开发工具。ZIP包含隐藏元数据、所有脚本、两种语言和说明。
包内 `SHA256SUMS.json` 覆盖除自身以外的文件，包外 `.zip.sha256` 覆盖整个ZIP。
没有执行 Git commit、push、发布或 Steam Workshop 上传。

# 中华实业 / Chinese Industrial Enterprises

**1.0.0 候选版 · Victoria 3 1.15.2 · 简体中文和英文**

八家架空中国企业，从农桑、矿业到铁路、电力和航空。它们通过游戏原版公司界面成立，按原版规则占用公司槽、经营、投资和取得繁荣奖励。大清、沿用中国国家定义的各政体、相应内战继承国及原版中央政府均可用，AI 中国也可按原版规则选择。

中华实业可单独启用，也可与《下南洋》《动员侨民》《洋务自强》同用。公司定义的成立条件无需额外 DLC。品牌商品沿用 **Charters of Commerce（商业宪章）** 的授权门槛，企业达到繁荣并实际经营相关产出后按游戏规则生产。

## 公司与成立条件

建筑等级按表内范围合计。鲁农的等级统计限本国的山东州，其他公司按全国计算。总部同时受游戏原版成立规则约束。

| 公司 | 基础经营 | 科技及规模 | 总部 | 繁荣奖励 | 声望商品 |
| --- | --- | --- | --- | --- | --- |
| 华兴实业 · Huaxing Industries | 汽车工业、工具工坊、钢铁厂、发动机厂、铁路、发电厂 | 炼钢技术，全国相关建筑 30 级 | 自由 | 全国建造效率 +10%，大学吞吐量 +10% | 华兴精密机械（工具） |
| 鲁农集团 · Shandong Agricultural Group | 小麦、水稻、黑麦、玉米、粟米农场，香蕉种植园 | 集约农业，山东相关建筑 20 级 | 山东 | 全国生活水平固定 +1 | 鲁农优质粮食（粮食） |
| 丰殖商号 · Fengzhi Trading House | 茶、咖啡、棉、丝、染料、糖、烟草、鸦片、橡胶种植园及葡萄园 | 集约农业，全国相关建筑 20 级 | 自由 | 表列十种建筑吞吐量各 +20% | 丰殖贡茶（茶叶） |
| 中华矿业总公司 · Chinese Mining Corporation | 煤、铁、铜、铅、硫、金矿 | 大气式蒸汽机，全国相关矿山 20 级 | 自由 | 六种矿山吞吐量各 +15% | 中华精煤（煤炭） |
| 中华石油公司 · Chinese Petroleum Company | 油井 | 抽油机，全国油井 15 级 | 自由 | 油井吞吐量 +20% | 中华石油（石油） |
| 华光电气公司 · Huaguang Electric Company | 发电厂、电气工业 | 发电技术，全国发电厂 15 级 | 自由 | 发电厂吞吐量 +15% | 华光电气设备（电话机） |
| 神州汽车制造公司 · Shenzhou Motor Works | 汽车工业和发动机厂 | 内燃机，全国两类建筑 20 级 | 自由 | 汽车工业和发动机厂吞吐量各 +20% | 神州牌汽车（汽车） |
| 凌云航空制造公司 · Lingyun Aviation Works | 具有飞机生产方式的汽车工业 | 军事航空，全国汽车工业 20 级 | 自由 | 汽车工业吞吐量 +20% | 凌云飞机（飞机） |

使用原版建筑层级的吞吐量修正，所以共享建筑采用其他生产方式时也会受益。生活水平 +1 加在财富决定的生活水平之上。八个商标为本项目独立设计，使用原生公司面板与背景。

## 安装

1. 解压 `chinese_industrial_enterprises.zip`。将其中的 `chinese_industrial_enterprises` 文件夹放进 `Victoria 3/mod` 用户数据目录。
2. 确认 Mod 目录直接包含隐藏的 `.metadata/metadata.json`。在 Paradox Launcher 中把「中华实业 · Chinese Industrial Enterprises」加入播放集并启用。
3. 使用 1.15.2 大清测试存档打开公司面板。首次验收可在独立播放集中仅启用本 Mod。 [快速本地验收](docs/VALIDATION.md)

## 测试与打包

以下命令从仓库根目录运行。游戏运行时只需 Victoria 3。重制商标需要 ImageMagick 7。

```sh
bash dev/chinese_industrial_enterprises/tools/build_logos.sh
python3 dev/chinese_industrial_enterprises/tools/package_mod.py
python3 -m unittest discover -s dev/chinese_industrial_enterprises/tests -v
python3 dev/chinese_industrial_enterprises/tools/package_mod.py --check
sha256sum -c chinese_industrial_enterprises.zip.sha256
```

Windows 可用 `Get-FileHash -Algorithm SHA256 chinese_industrial_enterprises.zip` 比对外部校验文件。完整经营与数值已通过静态检查，实际成立、品牌商品、繁荣效果和保存重载列入实机验收。超出原版常见三项的基础经营列表也需在本地确认。 [原生技术证据](docs/NATIVE_SCRIPT_REFERENCE.md) · [设计细节](docs/DESIGN.md) · [验证报告](docs/VALIDATION.md) · [版本记录](docs/CHANGELOG.md)

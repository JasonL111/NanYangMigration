# 下南洋 / Nanyang Migration

**1.1.3**（Victoria 3 **1.15.2**）。组织闽、粤、客家与汉人赴南洋安家。首航计划
**200,000 人**，每次成功后下一航次增加 **25%**，单次最多 **500,000 人**，成功后休整 **3 个游戏年**。
无需额外 DLC 或运行时依赖。三个航程结果事件均使用原创南洋港口插图。

- [正式安装包](nanyang_migration.zip) · [SHA-256](nanyang_migration.zip.sha256)
- [安装说明与迁移矩阵](nanyang_migration/README.md) · [版本记录](nanyang_migration/docs/CHANGELOG.md)
- [1.15 兼容性](nanyang_migration/docs/COMPATIBILITY_1_15.md) · [原生脚本参考](nanyang_migration/docs/NATIVE_SCRIPT_REFERENCE.md) · [验证报告](nanyang_migration/docs/VALIDATION.md)
- 安装包使用按事件画框比例裁切的 1280×696 DXT1 DDS。 [港口插图源文件](assets/nanyang_harbor.png)

## 动员侨民 / Overseas Chinese Mobilization

**1.0.0**（Victoria 3 **1.15.2**）。中国玩家可推动符合条件的外国接纳汉文化为主流文化。该 Mod 与《下南洋》分别安装，无前置依赖。

- [独立工程与安装说明](OverseasChineseMobilization/README.md)
- [动员侨民安装包](OverseasChineseMobilization/overseas_chinese_mobilization.zip) · [SHA-256](OverseasChineseMobilization/overseas_chinese_mobilization.zip.sha256)

## 下南洋开发

开发用的[独立诊断包](nanyang_native_probe.zip)不需要安装到正常游玩的播放集。

开发命令，从仓库根目录运行：

```sh
python3 tools/build_mod.py
python3 tools/build_probe.py
python3 -m unittest discover -s tests -v
python3 tools/package_mod.py
sha256sum -c nanyang_migration.zip.sha256 nanyang_native_probe.zip.sha256
```

Windows 可对 ZIP 使用 PowerShell `Get-FileHash -Algorithm SHA256`，与相应 `.sha256` 文件核对。游戏本体文件从未纳入安装包。

## 洋务自强 / Self-Strengthening Reform

**1.0.0 候选版**（Victoria 3 **1.15.2**）。1861 年起，地主 Clout 达到 20% 的中国君主制玩家可批准一次洋务改革，获得为期 20 年的三组政治力量与认同度修正。

- [安装说明与玩法](self_strengthening_reform/README.md) · [原生脚本参考](self_strengthening_reform/docs/NATIVE_SCRIPT_REFERENCE.md) · [验证报告](self_strengthening_reform/docs/VALIDATION.md)
- [洋务自强安装包](self_strengthening_reform.zip) · [SHA-256](self_strengthening_reform.zip.sha256)

《下南洋》《动员侨民》《洋务自强》均可单独安装，也可以在同一播放集中启用。

## 中华实业 / Chinese Industrial Enterprises

**1.0.0 候选版**（Victoria 3 **1.15.2**）。新增八家架空中国企业，经营范围覆盖农业、矿业、能源和近代工业。公司成立、投资和繁荣奖励沿用游戏原版系统。四个 Mod 都可单独安装。

- [公司一览与安装](chinese_industrial_enterprises/README.md) · [原生脚本参考](chinese_industrial_enterprises/docs/NATIVE_SCRIPT_REFERENCE.md) · [验证报告](chinese_industrial_enterprises/docs/VALIDATION.md)
- [中华实业安装包](chinese_industrial_enterprises.zip) · [SHA-256](chinese_industrial_enterprises.zip.sha256)

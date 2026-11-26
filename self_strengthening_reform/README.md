# 洋务自强 / Self-Strengthening Reform

**Mod 1.0.0 候选版 · Victoria 3 1.15.2 · 简体中文和英文。** 可单独安装，亦可与《下南洋》《动员侨民》同用。运行时只需游戏本体。

1860 年代兴起的洋务运动，通过兴办实业、整顿军备与广设学堂谋求自强。史实中的洋务诸臣与士绅关系密切。本 Mod 描绘一条架空路径，假设朝廷进一步开放仕途，使知识分子和实业家在二十年间取得更多政治影响。后续制度改革由玩家在原版立法系统中推进。

## 发动与效果

控制仍实行君主制的大清或合格的中国继承国，在日志「洋务自强」中选择「整顿旧制，推行新政」。从 **1861 年**起，地主的实际 **Clout 达到 20% 或以上**时，可以提出奏议。提出和批准时均检查玩家控制、国家资格与本局记录。

在事件「洋务诸臣，力陈积弊」中选择实施，即获得 **20 个游戏年**的「洋务新政」。选择暂缓会释放当前奏议，符合条件时可再次提议。实施成功后，整局只可使用一次，换国或改革期满后仍计为已使用。

| 利益集团 | 政治力量修正 | 认同度修正 |
| --- | ---: | ---: |
| 地主 | −50% | −5 点 |
| 知识分子 | +25% | +5 点 |
| 实业家 | +25% | +5 点 |

Clout 是集团在全国政治力量中的占比。表中的百分比修正该集团的政治力量，改革后的占比由游戏根据各集团的力量重新计算。事件对游戏数值的改动只有表中六项。

## 安装

1. 解压 `self_strengthening_reform.zip`。把其中的 `self_strengthening_reform` 文件夹放进 Victoria 3 用户数据的 `mod` 目录。Windows 默认位置为 `%USERPROFILE%\Documents\Paradox Interactive\Victoria 3\mod`。
2. 确认目录直接包含隐藏的 `.metadata/metadata.json`。在 Paradox Launcher 的播放集中启用「洋务自强 · Self-Strengthening Reform」。验收时使用只启用此 Mod 的播放集。
3. 使用 1.15.2 新开大清测试档，或复制一份已有的 1.15.2 存档。参照[游戏内验收步骤](docs/VALIDATION.md)检查奏议、修正与保存重载。

脚本按照存档级全局标记记录使用资格，并把限时修正挂在批准改革的国家。对已有存档中途启用、退订后重新启用及革命时限时修正的继承，仍须实机验证。建议将验收存档和正式存档分开。

## 开发与校验

在仓库根目录运行以下命令。打包和检查只使用 Python 标准库。

```sh
python3 dev/self_strengthening_reform/tools/package_mod.py
python3 -m unittest discover -s dev/self_strengthening_reform/tests -v
python3 dev/self_strengthening_reform/tools/package_mod.py --check
sha256sum -c self_strengthening_reform.zip.sha256
```

Windows 可用 PowerShell `Get-FileHash -Algorithm SHA256 self_strengthening_reform.zip` 与 `.sha256` 文件比对。

[功能设计](docs/DESIGN.md) · [1.15 原生证据](docs/NATIVE_SCRIPT_REFERENCE.md) · [验证报告与游戏内验收](docs/VALIDATION.md) · [版本记录](docs/CHANGELOG.md)

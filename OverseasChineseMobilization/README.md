# 动员侨民 / Overseas Chinese Mobilization

**1.0.0 · Victoria 3 1.15.2 · 独立 Mod**。执掌中国的玩家可以动员海外侨民。一个外国若不是霸权级、尚未以汉文化为主流文化，且汉、闽、粤、客家人口合计达到自身全国人口的40%，就可在保留既有主流文化的同时接纳汉文化。

[安装 ZIP](overseas_chinese_mobilization.zip) · [SHA-256](overseas_chinese_mobilization.zip.sha256) · [安装与完整玩法](overseas_chinese_mobilization/README.md)

项目自带简体中文和英文，无前置 Mod、额外 DLC 或外部运行时。下南洋可通过原版人口变化自然联动。两个 Mod 分别安装，彼此不调用脚本或共享状态。本项目没有包含任何 Victoria 3 游戏本体文件。

- [设计与边界](overseas_chinese_mobilization/docs/DESIGN.md)
- [原生脚本与插图证据](overseas_chinese_mobilization/docs/NATIVE_SCRIPT_REFERENCE.md)
- [验证报告](overseas_chinese_mobilization/docs/VALIDATION.md)
- [本地验收与40%测试方案](overseas_chinese_mobilization/docs/PLAYTEST.md)
- [更新记录](overseas_chinese_mobilization/docs/CHANGELOG.md)

## 开发与打包

```sh
python3 -m unittest discover -s tests -v
python3 tools/package_mod.py
sha256sum -c overseas_chinese_mobilization.zip.sha256
```

Windows 可运行 `Get-FileHash -Algorithm SHA256 overseas_chinese_mobilization.zip`，并对照 `.sha256` 中的哈希值。开发命令需要 Python 3.10 以上和标准库。原生脚本直接维护，打包不会生成或改写游戏逻辑。

`overseas_chinese_mobilization/` 是单独可安装目录。仓库的 `assets/` 保存会馆原画，`tests/` 和 `tools/` 是开发文件。安装包只包含 Mod 目录。

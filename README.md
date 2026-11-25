# 下南洋 / Nanyang Migration

**1.1.0 RC2**，目标游戏版本 **Victoria 3 1.15.2**。玩家可组织中国人口迁往南洋。使用原生 Paradox Script，安装与游戏运行无需 Python，无额外 DLC 要求。候选版已核对版本化脚本文档、通过静态和场景测试，真实引擎验收待完成。

- 正式玩法候选包：[nanyang_migration.zip](nanyang_migration.zip) · [SHA-256](nanyang_migration.zip.sha256)
- 独立小额诊断包：[nanyang_native_probe.zip](nanyang_native_probe.zip) · [SHA-256](nanyang_native_probe.zip.sha256)
- [安装、迁移机制与旧档](nanyang_migration/README.md) · [改动记录](nanyang_migration/docs/CHANGELOG.md)
- [1.15 兼容性调查](nanyang_migration/docs/COMPATIBILITY_1_15.md) · [原生脚本证据](nanyang_migration/docs/NATIVE_SCRIPT_REFERENCE.md) · [验证报告](nanyang_migration/docs/VALIDATION.md)

开发命令，从仓库根目录运行：

```sh
python3 tools/build_mod.py
python3 tools/build_probe.py
python3 -m unittest discover -s tests -v
python3 tools/package_mod.py
sha256sum -c nanyang_migration.zip.sha256 nanyang_native_probe.zip.sha256
```

Windows 可对 ZIP 使用 PowerShell `Get-FileHash -Algorithm SHA256`，与相应 `.sha256` 文件核对。游戏本体文件从未纳入安装包。

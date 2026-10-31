# 下南洋 / Nanyang Migration

Victoria 3 原生脚本 Mod，版本 **1.0.2**，目标游戏版本 **1.13.11 (Matcha)**。

- 安装目录：[nanyang_migration](nanyang_migration/)
- 安装包：`nanyang_migration.zip`
- 安装、机制及限制：[Mod README](nanyang_migration/README.md)
- 验证报告：[VALIDATION.md](nanyang_migration/docs/VALIDATION.md)

开发验证使用 `python3 -m unittest discover -s tests -v`。生成脚本为
`python3 tools/build_mod.py`，仅重建游戏脚本和数据表，不覆盖手写说明与验证证据。
游戏运行不需要 Python。没有修改游戏本体，也没有提交或推送 Git。

注意：本仓库产物已做静态和模拟执行测试，当前云环境没有 Victoria 3，
没有执行引擎加载及真实存档测试。请阅读验证报告中的未验证项。

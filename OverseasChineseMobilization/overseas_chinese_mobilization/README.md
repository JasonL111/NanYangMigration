# 动员侨民 / Overseas Chinese Mobilization

**Mod 1.0.0，目标 Victoria 3 1.15.2**。无需其他 Mod、DLC 或运行时依赖。

## 安装和启用

1. 解压安装包，将整个 `overseas_chinese_mobilization/` 放入 Victoria 3 的用户数据 `mod/` 目录。Windows 通常是 `文档/Paradox Interactive/Victoria 3/mod/`，macOS 通常是 `~/Documents/Paradox Interactive/Victoria 3/mod/`，Linux 通常是 `~/.local/share/Paradox Interactive/Victoria 3/mod/`。
2. 确认 `.metadata/metadata.json` 在 Mod 根目录，并且没有多嵌套一层同名文件夹。用启动器把「动员侨民」添加到当前播放集并启用。若启动器未列出手动安装项，可在 Mod 工具创建一个本地 Mod，再将本包内容放入对应目录。
3. 以玩家身份进入大清或符合资格的中国继承政权。在外交事务分组打开「动员侨民」日志。选中按钮可查看发动条件。

## 动员条件

- 中国身份依据国家定义 `CHI`、以 `CHI` 为来源的内战关系，以及原版中央政府指针（存在时）。大清、共和国和人民共和国的显示名称不参与判断。外国成为汉主流文化国家后仍不能发动。
- 统计外国自己所有实际领土上的 **汉、闽、粤、客家**总人口，包括劳动力与受抚养者、未整合州、海外州和分割州。人口须达到该国总人口的 **40%**，附庸国人口分别计算。
- 目标必须存续、有正人口、尚未将汉文化列入主流文化，且不属于霸权级 **Country Tier**。列强、未受承认国家及附庸均可成为目标。范围覆盖全球。
- 点击会为所有合格外国添加汉主流文化。既有主流文化与人口构成保留。原版法律和文化接纳规则继续决定当地文化待遇。
- 无使用次数限制、资源消耗或冷却。比例跌破40%后，已添加的文化由国家保留。若原版效果后来移除汉文化，且该国再次满足条件，可以再发动。

下南洋与本 Mod 独立安装。下南洋增加的侨民人口可通过原版人口统计使外国达到门槛。本 Mod 自身不改变人口。

## 存档和验收

本环境无 Victoria 3，真实引擎验收待执行。建议先用 1.15.2 的 1836 大清新档测试。加入进行中存档、卸载后的国家文化、保存重载、革命继承、国家形成、吞并后重新释放等行为由引擎决定，尚未分别验证。脚本不会自动撤销或恢复主流文化。

[本地验收和精确门槛测试](docs/PLAYTEST.md) · [验证范围](docs/VALIDATION.md) · [原生依据](docs/NATIVE_SCRIPT_REFERENCE.md)

### English installation

Place the complete `overseas_chinese_mobilization` folder in the Victoria 3 user-data `mod` directory, including `.metadata`. Enable **Overseas Chinese Mobilization** in the Launcher. Play China or an eligible successor and open **Mobilize the Overseas Chinese** in the Journal. The action recognizes Han in all qualifying foreign countries once the four specified cultures make up at least 40% of their own total population. It preserves existing primary cultures and has no cost or cooldown.

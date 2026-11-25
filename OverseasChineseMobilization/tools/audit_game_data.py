"""Find the required base-game identifiers without modifying or copying game files."""

import argparse
from pathlib import Path
import re

CHECKS = {
    "common/cultures": ("han", "min", "yue", "hakka"),
    "common/country_definitions": ("CHI",),
    "common/journal_entry_groups": ("je_group_foreign_affairs",),
}


def game_files(folder):
    for path in sorted(folder.glob("*.txt")):
        yield path, path.read_text(encoding="utf-8-sig", errors="replace")


def audit(game):
    missing = []
    for folder, ids in CHECKS.items():
        files = list(game_files(game / folder))
        for key in ids:
            pattern = rf"^[ \t]*{re.escape(key)}[ \t]*=[ \t]*\{{"
            match = next((p for p, s in files if re.search(pattern, s, re.M)), None)
            if match:
                print(f"{key}: {match.relative_to(game)}")
            else:
                missing.append(key)

    for path, text in game_files(game / "common/country_definitions"):
        if re.search(r"^[ \t]*tier[ \t]*=[ \t]*hegemony\b", text, re.M):
            print(f"tier = hegemony: {path.relative_to(game)}")
            break
    else:
        missing.append("tier = hegemony")

    for folder in ("events", "common/scripted_effects", "common/journal_entries"):
        for path in sorted((game / folder).rglob("*.txt")):
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            if re.search(r"set_global_variable\s*=\s*\{[^}]*\bname\s*=\s*chinese_central_government\b", text):
                print(f"Central government writer: {path.relative_to(game)}")
    if missing:
        raise SystemExit("Unresolved IDs: " + ", ".join(missing))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path, help="Victoria 3 installation's game directory")
    audit(parser.parse_args().game)

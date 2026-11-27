#!/usr/bin/env bash
set -euo pipefail

project_dir=$(cd -- "$(dirname -- "$0")/.." && pwd)
repo_dir=$(cd -- "$project_dir/../.." && pwd)
icon_dir="$repo_dir/chinese_industrial_enterprises/gfx/interface/icons/company_icons"
scratch=$(mktemp -d)
trap 'rm -rf -- "$scratch"' EXIT
mkdir -p "$icon_dir"

logos=(huaxing shandong fengzhi mining petroleum huaguang shenzhou lingyun)
for sheet in 1 2; do
    magick "$project_dir/assets/cie_seals_$sheet.png" -crop 2x2@ +repage "$scratch/sheet-$sheet-%d.png"
done
for index in "${!logos[@]}"; do
    sheet=$((index / 4 + 1))
    cell=$((index % 4))
    icon="$icon_dir/cie_${logos[index]}.dds"
    magick "$scratch/sheet-$sheet-$cell.png" -background none -alpha on \
        -fuzz 3% -trim +repage -resize 232x232 -gravity center -extent 256x256 \
        -define dds:compression=dxt5 -define dds:mipmaps=0 "$icon"
    magick "$icon" null:
    magick identify -format '%f %wx%h %[channels]\n' "$icon"
done

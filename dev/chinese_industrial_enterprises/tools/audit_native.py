"""Check the release definitions against the published 1.15.2 vanilla snapshot and engine logs."""

import argparse
from collections.abc import Iterator
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

from package_mod import MOD


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_records(source):
    return dict(re.findall(r"(?ms)^(cie_\w+) = \{\n(.*?)^}", source))


def vanilla_table(root, key):
    return {name: entry[1] for name, entry in json.loads((root / f"common/{key}.json").read_bytes()).items()}


def value(record, key, default=None):
    return record.get(key, ("=", default))[1]


def clauses(node) -> Iterator[tuple]:
    if isinstance(node, dict):
        for key, (_, item) in node.items():
            yield key, item
            yield from clauses(item)


def audit(snapshot, digest):
    manifest = snapshot / "manifest.json"
    version = json.loads(manifest.read_bytes())["game_version"]
    require(version == "1.15.2", f"Expected 1.15.2 vanilla data, got {version}")
    native = digest / version
    modifier_log = native / "docs/modifiers.log"
    registry = set(re.findall(r"(?m)^([a-zA-Z0-9_]+):$", modifier_log.read_text(encoding="utf-8")))
    doc = (native / "types/companies.md").read_text(encoding="utf-8-sig")
    for field in ("potential", "attainable", "possible", "can_establish_in", "prosperity_modifier",
                  "building_types", "possible_prestige_goods", "prestige_goods_trigger", "ai_will_do"):
        require(re.search(rf"(?m)^\s*{field} = \{{", doc), f"Company type field missing: {field}")

    buildings = vanilla_table(snapshot, "buildings")
    techs = vanilla_table(snapshot, "technologies")
    goods = vanilla_table(snapshot, "goods")
    pm_groups = vanilla_table(snapshot, "pm_groups")
    pms = vanilla_table(snapshot, "pms")
    stock_companies = vanilla_table(snapshot, "company_types")
    stock_brands = vanilla_table(snapshot, "prestige_goods")
    journals = vanilla_table(snapshot, "journal_entries")
    backgrounds = {value(company, "background") for company in stock_companies.values()}
    states = json.loads((snapshot / "history/states.json").read_bytes())["00_states.txt"]
    require("CHI" in {part["country"] for part in states["STATE_SHANDONG"]["parts"]}, "Shandong history differs")
    require("global_var:chinese_central_government" in str(journals["je_reunify_china"]),
            "Vanilla central-government link changed")
    require(value(goods["electricity"], "local") == "yes", "Electricity local-good classification changed")
    require(value(buildings["building_gold_field"], "can_switch_owner") == "no", "Gold fields changed")
    require(value(buildings["building_gold_mine"], "ownership_type") == "self", "Gold mine ownership changed")
    require(value(value(stock_brands["prestige_good_ford_automobiles"], "possible"), "has_dlc_feature")
            == "mp1_content", "Vanilla prestige gate changed")

    def outputs(building):
        for group in value(buildings[building], "production_method_groups", []):
            for pm in value(pm_groups[group], "production_methods", []):
                for key, amount in clauses(pms[pm]):
                    if key.startswith("goods_output_") and key.endswith("_add") and Decimal(amount) > 0:
                        yield key.removeprefix("goods_output_").removesuffix("_add")

    company_source = MOD / "common/company_types/cie_companies.txt"
    brand_source = MOD / "common/prestige_goods/cie_brands.txt"
    companies = read_records(company_source.read_text(encoding="utf-8"))
    brands = read_records(brand_source.read_text(encoding="utf-8"))
    required_base = set()
    required_modifiers = set()
    for name, company in companies.items():
        roster = re.search(r"building_types = \{([^}]+)\}", company)[1].split()
        technology = re.search(r"has_technology_researched = (\w+)", company)[1]
        background = re.search(r'background = ("[^"]+")', company)[1]
        modifiers = set(re.findall(r"(?m)^\s+((?:state|building)_\w+) = -?\d", company))
        brand = re.search(r"possible_prestige_goods = \{ (cie_\w+) \}", company)[1]
        good = re.search(r"base_good = (\w+)", brands[brand])[1]
        require(set(roster) <= buildings.keys(), f"{name}: unregistered building")
        require(technology in techs, f"{name}: unregistered technology")
        require(background in backgrounds, f"{name}: background absent from stock company data")
        require(modifiers <= registry, f"{name}: unknown modifier {modifiers - registry}")
        require(good in goods and value(goods[good], "local") != "yes", f"{name}: invalid base good")
        require(any(good in set(outputs(building)) for building in roster),
                f"{name}: no roster building produces {good}")
        if name == "cie_chinese_mining_corporation":
            native_mines = {b for b, definition in buildings.items() if value(definition, "building_group") == "bg_mining"}
            require(set(roster) == native_mines, "Vanilla conventional mine roster differs")
        required_base.update(roster)
        required_modifiers.update(modifiers)
        print(f"{name}: {len(roster)} building types, {technology}, {good}")

    require("military_aviation" in value(pms["pm_aeroplane_production"], "unlocking_technologies"),
            "Aircraft technology changed")
    require("combustion_engine" in value(pms["pm_automobile_production"], "unlocking_technologies"),
            "Automobile technology changed")
    print(f"{len(companies)} companies, {len(required_base)} unique buildings, "
          f"{len(required_modifiers)} registered modifiers, {len(brands)} producible prestige base goods")
    for path in (manifest, modifier_log):
        print(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path, help="The versioned vanilla_parsed directory")
    parser.add_argument("digest", type=Path, help="The Modding-Digests checkout")
    args = parser.parse_args()
    audit(args.snapshot, args.digest)

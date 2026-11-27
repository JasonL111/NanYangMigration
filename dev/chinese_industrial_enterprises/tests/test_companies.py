from dataclasses import dataclass
from decimal import Decimal
from hashlib import sha256
import json
from pathlib import Path
import re
import struct
import tempfile
import unittest
import zipfile
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from package_mod import ARCHIVE, CHECKSUM, MOD, source_files, write_archive


TOKEN = re.compile(r'#[^\n]*|"(?:[^"\\]|\\.)*"|[{}]|[<>!?]=|[=<>]|[^\s{}"#=<>!?]+')
OPERATORS = {"=", "?=", ">", ">=", "<", "<=", "!="}


def parse(text):
    """Read the assignments and literal lists used in this Mod."""
    tokens = [t for t in TOKEN.findall(text) if not t.startswith("#")]

    def block(index, nested):
        entries = []
        while index < len(tokens):
            key = tokens[index]
            index += 1
            if key == "}":
                if not nested:
                    raise ValueError("Unexpected closing brace")
                return entries, index
            if key in OPERATORS or key == "{":
                raise ValueError(f"Unexpected token: {key}")
            if index == len(tokens) or tokens[index] not in OPERATORS:
                entries.append(key)
                continue
            operator, value = tokens[index:index + 2]
            index += 2
            if value == "{":
                value, index = block(index, True)
            elif value == "}" or value in OPERATORS:
                raise ValueError(f"Missing value for {key}")
            entries.append((key, operator, value))
        if nested:
            raise ValueError("Missing closing brace")
        return entries, index

    return block(0, False)[0]


def fields(block):
    fields = {}
    for key, op, value in block:
        if op != "=" or key in fields:
            raise ValueError(f"Expected one assignment per field: {key}")
        fields[key] = value
    return fields


def throughput(buildings, amount):
    return {f"building_{building}_throughput_add": Decimal(amount) for building in buildings}


GRAIN_FARMS = ("wheat_farm", "rice_farm", "rye_farm", "maize_farm", "millet_farm", "banana_plantation")
CASH_CROPS = (
    "tea_plantation", "coffee_plantation", "cotton_plantation", "silk_plantation", "dye_plantation",
    "sugar_plantation", "tobacco_plantation", "opium_plantation", "rubber_plantation", "vineyard",
)
MINES = ("coal_mine", "iron_mine", "copper_mine", "lead_mine", "sulfur_mine", "gold_mine")
AUTOMOTIVE = ("automotive_industry", "motor_industry")


@dataclass(frozen=True)
class CompanySpec:
    chinese: str
    english: str
    technology: str
    buildings: tuple
    levels: int
    rewards: dict
    brand: str
    good: str
    total: str = ""


SPECS = {
    "huaxing_industries": CompanySpec(
        "华兴实业", "Huaxing Industries", "steelworking",
        ("automotive_industry", "tooling_workshop", "steel_mill", "motor_industry", "shipyard", "railway", "power_plant"),
        30, {"state_construction_mult": Decimal("0.10"), "building_university_throughput_add": Decimal("0.10")},
        "huaxing_precision_machinery", "tools", "huaxing",
    ),
    "shandong_agricultural_group": CompanySpec(
        "鲁农集团", "Shandong Agricultural Group", "intensive_agriculture", GRAIN_FARMS,
        20, {"state_standard_of_living_add": Decimal(1)}, "shandong_premium_grain", "grain", "shandong",
    ),
    "fengzhi_trading_house": CompanySpec(
        "丰殖商号", "Fengzhi Trading House", "intensive_agriculture", CASH_CROPS,
        20, throughput(CASH_CROPS, "0.20"), "fengzhi_imperial_tea", "tea", "fengzhi",
    ),
    "chinese_mining_corporation": CompanySpec(
        "中华矿业总公司", "Chinese Mining Corporation", "atmospheric_engine", MINES,
        20, throughput(MINES, "0.15"), "chinese_premium_coal", "coal", "mining",
    ),
    "chinese_petroleum_company": CompanySpec(
        "中华石油公司", "Chinese Petroleum Company", "pumpjacks", ("oil_rig",),
        15, throughput(("oil_rig",), "0.20"), "chinese_premium_petroleum", "oil",
    ),
    "huaguang_electric_company": CompanySpec(
        "华光电气公司", "Huaguang Electric Company", "electrical_generation", ("power_plant", "electrics_industry"),
        15, throughput(("power_plant",), "0.15"), "huaguang_electric_apparatus", "telephones",
    ),
    "shenzhou_motor_works": CompanySpec(
        "神州汽车制造公司", "Shenzhou Motor Works", "combustion_engine", AUTOMOTIVE,
        20, throughput(AUTOMOTIVE, "0.20"), "shenzhou_motorcars", "automobiles", "shenzhou",
    ),
    "lingyun_aviation_works": CompanySpec(
        "凌云航空制造公司", "Lingyun Aviation Works", "military_aviation", ("automotive_industry",),
        20, throughput(("automotive_industry",), "0.20"), "lingyun_aircraft", "aeroplanes",
    ),
}

COMMON_FILES = {
    "company_types/cie_companies.txt", "prestige_goods/cie_brands.txt",
    "script_values/cie_building_levels.txt", "scripted_triggers/cie_company_triggers.txt",
}


class CompanyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.common = MOD / "common"
        source = {name: (cls.common / name).read_text(encoding="utf-8") for name in COMMON_FILES}
        cls.companies = {k: fields(v) for k, v in fields(parse(source["company_types/cie_companies.txt"])).items()}
        cls.brands = {k: fields(v) for k, v in fields(parse(source["prestige_goods/cie_brands.txt"])).items()}
        cls.values = fields(parse(source["script_values/cie_building_levels.txt"]))
        cls.triggers = fields(parse(source["scripted_triggers/cie_company_triggers.txt"]))
        cls.scripts = "\n".join(source.values())

    def test_metadata_namespace_and_independence(self):
        data = json.loads((MOD / ".metadata/metadata.json").read_bytes())
        self.assertEqual((data["id"], data["version"], data["supported_game_version"]),
                         (MOD.name, "1.0.0", "1.15.2"))
        self.assertEqual(data["relationships"], [])
        self.assertNotIn("replace_path", data)
        paths = {path.relative_to(self.common).as_posix() for path in self.common.rglob("*.txt")}
        self.assertEqual(paths, COMMON_FILES)
        self.assertNotRegex(self.scripts, r"\b(?:nym_|ocm_|ssr_|replace_path|INJECT:|REPLACE:|on_action)")
        self.assertEqual(set(self.companies), {"cie_" + key for key in SPECS})
        self.assertEqual(set(self.brands), {"cie_" + spec.brand for spec in SPECS.values()})
        self.assertEqual(set(self.values), {f"cie_{s.total}_levels" for s in SPECS.values() if s.total})
        self.assertEqual(set(self.triggers), {"cie_chinese_country", "cie_shandong_headquarters"})

    def test_country_identity_and_ai(self):
        self.assertEqual(self.triggers["cie_chinese_country"], parse("""
            is_country_alive = yes
            OR = {
                country_definition = cd:CHI
                AND = {
                    exists = civil_war_origin_country
                    civil_war_origin_country ?= { country_definition = cd:CHI }
                }
                AND = {
                    has_global_variable = chinese_central_government
                    global_var:chinese_central_government ?= this
                }
            }
        """))
        for company in self.companies.values():
            self.assertEqual(company["potential"], parse("cie_chinese_country = yes"))
            self.assertEqual(company["ai_will_do"], parse("always = yes"))
            self.assertEqual(company["flavored_company"], "yes")

    def test_building_types_and_prosperity(self):
        for name, spec in SPECS.items():
            with self.subTest(company=name):
                company = self.companies["cie_" + name]
                self.assertCountEqual(company["building_types"], ["building_" + b for b in spec.buildings])
                actual = fields(company["prosperity_modifier"])
                self.assertEqual({k: Decimal(v) for k, v in actual.items()}, spec.rewards)
                optional_hq = {"can_establish_in"} if spec.total == "shandong" else set()
                self.assertEqual(set(company), {
                    "icon", "background", "flavored_company", "building_types", "potential", "attainable",
                    "possible", "prosperity_modifier", "possible_prestige_goods", "prestige_goods_trigger", "ai_will_do",
                } | optional_hq)

    def test_tech_aggregate_counts_and_headquarters(self):
        self.assertEqual(self.triggers["cie_shandong_headquarters"], parse("state_region = s:STATE_SHANDONG"))
        for name, spec in SPECS.items():
            with self.subTest(company=name):
                company = self.companies["cie_" + name]
                self.assertEqual(company["attainable"], parse(f"has_technology_researched = {spec.technology}"))
                if spec.total:
                    checks = " ".join(f"is_building_type = building_{b}" for b in spec.buildings)
                    self.assertEqual(self.values[f"cie_{spec.total}_levels"], parse(f"""
                        value = 0
                        every_scope_building = {{
                            limit = {{ OR = {{ {checks} }} }}
                            add = level
                        }}
                    """))
                    scope_check = f"cie_{spec.total}_levels >= {spec.levels}"
                    if spec.total == "shandong":
                        scope_check = f"any_scope_state = {{ cie_shandong_headquarters = yes {scope_check} }}"
                        self.assertEqual(company["can_establish_in"], parse("cie_shandong_headquarters = yes"))
                    expected = f"custom_tooltip = {{ text = cie_{spec.total}_levels_tt {scope_check} }}"
                else:
                    expected = ("country_has_building_type_levels = { "
                                f"target = bt:building_{spec.buildings[0]} value >= {spec.levels} }}")
                self.assertEqual(company["possible"], parse(expected))

    def test_prestige_goods_use_native_optional_gate(self):
        for name, spec in SPECS.items():
            with self.subTest(company=name):
                company = self.companies["cie_" + name]
                brand_key = "cie_" + spec.brand
                self.assertEqual(company["possible_prestige_goods"], [brand_key])
                self.assertEqual(company["prestige_goods_trigger"], parse("company_is_prosperous = yes"))
                self.assertEqual(self.brands[brand_key], {
                    "possible": parse("has_dlc_feature = mp1_content"),
                    "base_good": spec.good, "prestige_bonus": "0.1", "texture": company["icon"],
                })

    def test_bilingual_names_descriptions_and_tooltips(self):
        keys = set(self.companies) | set(self.brands)
        expected_keys = keys | {key + "_desc" for key in keys}
        expected_keys |= {f"cie_{spec.total}_levels_tt" for spec in SPECS.values() if spec.total}
        for index, lang in enumerate(("simp_chinese", "english")):
            with self.subTest(language=lang):
                raw = (MOD / f"localization/{lang}/cie_l_{lang}.yml").read_bytes()
                self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
                header, *entries = raw.decode("utf-8-sig").splitlines()
                self.assertEqual(header, f"l_{lang}:")
                translations = {}
                for line in entries:
                    match = re.fullmatch(r' (cie_\w+):0 "((?:[^"\\]|\\.)+)"', line)
                    self.assertIsNotNone(match, line)
                    self.assertNotIn(match[1], translations)
                    translations[match[1]] = match[2]
                self.assertEqual(set(translations), expected_keys)
                for name, spec in SPECS.items():
                    self.assertEqual(translations["cie_" + name], (spec.chinese, spec.english)[index])
                self.assertNotIn("华兴实业总公司", translations.values())
                self.assertNotIn("天物商号", translations.values())

    def test_logos_have_distinct_bc3_textures(self):
        hashes = set()
        icons = {company["icon"].strip('"') for company in self.companies.values()}
        self.assertEqual(len(icons), 8)
        for icon in icons:
            self.assertRegex(icon, r"^gfx/interface/icons/company_icons/cie_\w+\.dds$")
            data = (MOD / icon).read_bytes()
            self.assertEqual(data[:8], b"DDS |\x00\x00\x00")
            self.assertEqual(struct.unpack_from("<II", data, 12), (256, 256))
            self.assertEqual(data[84:88], b"DXT5")
            self.assertEqual(len(data), 128 + 64 * 64 * 16)
            hashes.add(sha256(data).hexdigest())
        self.assertEqual(len(hashes), 8)


class ArchiveTests(unittest.TestCase):
    def test_zip_crc_paths_bytes_and_sha256(self):
        expected = {f"{MOD.name}/{p.relative_to(MOD).as_posix()}" for p in MOD.rglob("*") if p.is_file()}
        with zipfile.ZipFile(ARCHIVE) as archive:
            self.assertIsNone(archive.testzip())
            self.assertCountEqual(archive.namelist(), expected)
            for name in expected:
                self.assertEqual(archive.read(name), (MOD.parent / name).read_bytes())
        self.assertEqual(CHECKSUM.read_text(encoding="ascii"),
                         f"{sha256(ARCHIVE.read_bytes()).hexdigest()}  {ARCHIVE.name}\n")

    def test_reproducible_packaging(self):
        with tempfile.TemporaryDirectory() as temp:
            other = Path(temp) / ARCHIVE.name
            write_archive(source_files(), other)
            self.assertEqual(ARCHIVE.read_bytes(), other.read_bytes())


if __name__ == "__main__":
    unittest.main()

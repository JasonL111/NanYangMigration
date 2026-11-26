import hashlib
import json
from pathlib import Path
import re
import struct
import sys
import unittest
import zipfile


sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from package_mod import ARCHIVE, CHECKSUM, MOD, build_bytes, release_sources


TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|#[^\n]*|[{}]|[<>!?]=|[=<>]|[^\s"{}#=<>!?]+')
COMPARISON = {"=", "?=", ">=", "<=", ">", "<", "!="}


def parse(script):
    """Read assignments and braces in these five scripts, without evaluating them."""
    tokens = [token for token in TOKEN.findall(script) if not token.startswith("#")]

    def read_block(index, nested=False):
        statements = []
        while index < len(tokens):
            if tokens[index] == "}":
                if not nested:
                    raise ValueError("Unexpected closing brace")
                return statements, index + 1
            key, operator, value = tokens[index:index + 3]
            if key in COMPARISON | {"{"} or operator not in COMPARISON:
                raise ValueError(f"Invalid assignment: {key} {operator} {value}")
            index += 3
            if value == "{":
                value, index = read_block(index, nested=True)
            elif value in COMPARISON | {"}"}:
                raise ValueError(f"Missing value for {key}")
            statements.append((key, operator, value))
        if nested:
            raise ValueError("Missing closing brace")
        return statements, index

    return read_block(0)[0]


def get(block, key):
    (value,) = [value for name, operator, value in block if name == key and operator == "="]
    return value


def walk(block):
    for key, operator, value in block:
        yield key, operator, value
        if isinstance(value, list):
            yield from walk(value)


SCRIPTS = {
    "journal": "common/journal_entries/ssr_journal.txt",
    "buttons": "common/scripted_buttons/ssr_buttons.txt",
    "triggers": "common/scripted_triggers/ssr_conditions.txt",
    "modifiers": "common/static_modifiers/ssr_modifiers.txt",
    "events": "events/ssr_reform_events.txt",
}


class ScriptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {name: (MOD / path).read_text(encoding="utf-8") for name, path in SCRIPTS.items()}
        cls.scripts = {name: parse(source) for name, source in cls.sources.items()}
        cls.triggers = cls.scripts["triggers"]
        cls.journal = get(cls.scripts["journal"], "ssr_je_reform")
        cls.button = get(cls.scripts["buttons"], "ssr_reform_button")
        cls.event = get(cls.scripts["events"], "self_strengthening_reform.1")

    def test_metadata_and_independent_runtime(self):
        data = json.loads((MOD / ".metadata/metadata.json").read_bytes())
        self.assertEqual(data["id"], MOD.name)
        self.assertEqual(data["version"], "1.0.0")
        self.assertEqual(data["supported_game_version"], "1.15.2")
        self.assertEqual(data["relationships"], [])
        self.assertNotIn("replace_path", data)
        paths = {path.relative_to(MOD).as_posix() for path in MOD.rglob("*.txt")}
        self.assertEqual(paths, set(SCRIPTS.values()))
        self.assertNotRegex("\n".join(self.sources.values()), r"\b(?:nym_|ocm_|nanyang_migration|overseas_chinese_mobilization|has_dlc)")
        for name, script in self.scripts.items():
            if name == "events":
                self.assertEqual(get(script, "namespace"), "self_strengthening_reform")
                self.assertEqual({key for key, _, _ in script}, {"namespace", "self_strengthening_reform.1"})
            else:
                self.assertTrue(all(key.startswith("ssr_") for key, _, _ in script), name)

    def test_country_identity_and_monarchy(self):
        self.assertEqual(get(self.triggers, "ssr_player_chinese_monarchy"), parse("""
            is_player = yes
            is_country_alive = yes
            has_law = law_type:law_monarchy
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

    def test_inclusive_year_and_landowner_clout_gates(self):
        checks = {(key, operator, value) for key, operator, value in walk(
            get(self.triggers, "ssr_can_enact_reform")) if isinstance(value, str)}
        self.assertIn(("ssr_player_chinese_monarchy", "=", "yes"), checks)
        self.assertIn(("year", ">=", "1861"), checks)
        self.assertIn(("exists", "=", "ig:ig_landowners"), checks)
        self.assertIn(("has_global_variable", "=", "ssr_reform_enacted"), checks)
        self.assertIn(("has_modifier", "=", "ssr_reforms"), checks)
        self.assertIn(
            ("ig:ig_landowners", "?=", parse("ig_clout >= 0.20")),
            list(walk(get(self.triggers, "ssr_can_enact_reform"))),
        )
        self.assertIn(
            ("NOR", "=", parse("has_global_variable = ssr_reform_enacted has_modifier = ssr_reforms")),
            list(walk(get(self.triggers, "ssr_can_enact_reform"))),
        )

    def test_journal_button_and_outcome_references(self):
        self.assertEqual(get(self.journal, "context"), "country")
        self.assertEqual(get(self.journal, "group"), "je_group_internal_affairs")
        self.assertEqual(get(self.journal, "scripted_button"), "ssr_reform_button")
        self.assertEqual(get(self.journal, "can_deactivate"), "yes")
        self.assertEqual(get(self.journal, "can_revolution_inherit"), "yes")
        self.assertEqual(get(self.journal, "possible"), parse("ssr_player_chinese_monarchy = yes"))
        visible = parse("ssr_player_chinese_monarchy = yes NOT = { has_global_variable = ssr_reform_enacted }")
        self.assertEqual(get(self.journal, "is_shown_when_inactive"), visible)
        self.assertEqual(get(self.button, "visible"), visible)
        outcome = get(self.journal, "outcome")
        self.assertEqual(get(outcome, "trigger"), parse("has_global_variable = ssr_reform_enacted"))
        self.assertNotIn("effect", {key for key, _, _ in outcome})
        self.assertFalse({"complete", "on_complete", "invalid", "fail", "modifiers_while_active"}.intersection(
            key for key, _, _ in self.journal))

    def test_button_rechecks_player_and_pending_before_dispatch(self):
        self.assertEqual(get(self.button, "ai_chance"), parse("base = 0"))
        self.assertNotIn("autocomplete", {key for key, _, _ in self.button})
        self.assertEqual(get(self.button, "possible"), parse("ssr_can_submit_petition = yes"))
        self.assertEqual(get(self.triggers, "ssr_can_submit_petition"), parse("""
            ssr_can_enact_reform = yes
            custom_tooltip = {
                text = ssr_requires_no_open_petition
                NOT = {
                    AND = {
                        has_global_variable = ssr_petition_country
                        global_var:ssr_petition_country ?= { is_country_alive = yes }
                    }
                }
            }
        """))
        self.assertEqual(get(self.button, "effect"), parse("""
            custom_tooltip = ssr_open_petition_tt
            hidden_effect = {
                if = {
                    limit = { ssr_can_submit_petition = yes }
                    set_global_variable = { name = ssr_petition_country value = this days = 94 }
                    trigger_event = { id = self_strengthening_reform.1 popup = yes }
                }
            }
        """))

    def test_enact_deferral_and_cleanup(self):
        self.assertEqual(get(self.event, "type"), "country_event")
        self.assertEqual(get(self.event, "duration"), "3")
        self.assertEqual(get(self.triggers, "ssr_owns_petition"), parse("""
            has_global_variable = ssr_petition_country
            global_var:ssr_petition_country ?= this
        """))
        enact, defer = [option for key, _, option in self.event if key == "option"]
        self.assertEqual(enact, parse("""
            name = ssr_reform_enact
            trigger = {
                ssr_owns_petition = yes
                ssr_can_enact_reform = yes
            }
            ai_chance = { base = 0 }
            if = {
                limit = { ssr_owns_petition = yes }
                if = {
                    limit = { ssr_can_enact_reform = yes }
                    add_modifier = { name = ssr_reforms years = 20 }
                    hidden_effect = {
                        if = {
                            limit = { has_modifier = ssr_reforms }
                            set_global_variable = ssr_reform_enacted
                        }
                    }
                }
                hidden_effect = { remove_global_variable = ssr_petition_country }
            }
        """))
        self.assertEqual(defer, parse("""
            name = ssr_reform_defer
            default_option = yes
            ai_chance = { base = 1 }
            custom_tooltip = ssr_reform_defer_tt
            hidden_effect = {
                if = {
                    limit = { ssr_owns_petition = yes }
                    remove_global_variable = ssr_petition_country
                }
            }
        """))
        self.assertEqual({key for key, _, _ in self.event},
                         {"type", "title", "desc", "duration", "event_image", "option"})

    def test_six_group_specific_modifiers_only(self):
        self.assertEqual(get(self.scripts["modifiers"], "ssr_reforms"), parse("""
            icon = "gfx/interface/icons/timed_modifier_icons/modifier_flag_positive.dds"
            interest_group_ig_landowners_pol_str_mult = -0.50
            interest_group_ig_intelligentsia_pol_str_mult = 0.25
            interest_group_ig_industrialists_pol_str_mult = 0.25
            interest_group_ig_landowners_approval_add = -5
            interest_group_ig_intelligentsia_approval_add = 5
            interest_group_ig_industrialists_approval_add = 5
        """))

    def test_bilingual_bom_and_localization_references(self):
        keys = {"ssr_je_reform", "ssr_je_reform_reason", "ssr_reforms"}
        for category in ("journal", "buttons", "triggers", "events"):
            for key, _, value in walk(self.scripts[category]):
                if key in {"header", "effect_header", "conclusion_desc", "title", "desc", "text", "custom_tooltip", "name"}:
                    if isinstance(value, str) and value not in {"ssr_petition_country", "ssr_reforms"}:
                        keys.add(value)
        for language in ("english", "simp_chinese"):
            with self.subTest(language=language):
                path = MOD / f"localization/{language}/ssr_l_{language}.yml"
                self.assertTrue(path.read_bytes().startswith(b"\xef\xbb\xbf"))
                header, *lines = path.read_text(encoding="utf-8-sig").splitlines()
                self.assertEqual(header, f"l_{language}:")
                found = []
                for line in lines:
                    match = re.fullmatch(r' (ssr_\w+):0 "(?:\\.|[^"\\])*"', line)
                    self.assertIsNotNone(match, line)
                    found.append(match[1])
                self.assertCountEqual(found, keys)

    def test_event_image_dds(self):
        reference = get(get(self.event, "event_image"), "texture").strip('"')
        self.assertEqual(reference, "gfx/event_pictures/ssr_reform_council.dds")
        texture = (MOD / reference).read_bytes()
        self.assertEqual(texture[:8], b"DDS |\x00\x00\x00")
        height, width = struct.unpack_from("<II", texture, 12)
        self.assertEqual((width, height), (1280, 960))
        self.assertEqual(texture[84:88], b"DXT1")
        self.assertEqual(len(texture), 128 + (width // 4) * (height // 4) * 8)


class PackageTests(unittest.TestCase):
    def test_zip_bytes_crc_and_sha256(self):
        expected_paths = {
            f"{MOD.name}/{path.relative_to(MOD).as_posix()}"
            for path in MOD.rglob("*") if path.is_file()
        }
        with zipfile.ZipFile(ARCHIVE) as zip_file:
            self.assertIsNone(zip_file.testzip())
            self.assertCountEqual(zip_file.namelist(), expected_paths)
            for name in expected_paths:
                self.assertEqual(zip_file.read(name), (MOD.parent / name).read_bytes(), name)
        digest = hashlib.sha256(ARCHIVE.read_bytes()).hexdigest()
        self.assertEqual(CHECKSUM.read_text(encoding="ascii"), f"{digest}  {ARCHIVE.name}\n")

    def test_reproducible_zip(self):
        self.assertEqual(build_bytes(release_sources()), ARCHIVE.read_bytes())


if __name__ == "__main__":
    unittest.main()

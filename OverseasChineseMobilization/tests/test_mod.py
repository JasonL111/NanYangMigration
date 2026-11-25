"""Static contracts and integer business logic. This is not an engine emulator."""

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_CEILING
import json
from pathlib import Path
import re
from struct import unpack_from
import unittest

PROJECT = Path(__file__).resolve().parents[1]
MOD = PROJECT / "overseas_chinese_mobilization"
COMMON = MOD / "common"


def parse_script(path):
    """Parse the assignments used by this project, retaining repeated keys."""
    source = path.read_text(encoding="utf-8")
    tokens = list(re.finditer(r'"(?:\\.|[^"\\])*"|#[^\n]*|\s+|\?=|>=|<=|!=|[{}=<>]|[^\s"{}=<>!?#]+', source))
    if "".join(t[0] for t in tokens) != source:
        raise ValueError(f"Unrecognized token in {path}")
    words = [t[0] for t in tokens if not (t[0].isspace() or t[0].startswith("#"))]

    def block(i, nested=False):
        fields = []
        while i < len(words):
            if words[i] == "}":
                if not nested:
                    raise ValueError(f"Unexpected closing brace in {path}")
                return fields, i + 1
            if i + 2 >= len(words) or words[i+1] not in {"=", "?=", ">=", "<=", "<", ">", "!="}:
                raise ValueError(f"Expected assignment at {words[i]} in {path}")
            key, op, value = words[i:i+3]
            i += 3
            if value == "{":
                value, i = block(i, True)
            elif value == "}":
                raise ValueError(f"Missing value for {key} in {path}")
            fields.append((key, op, value))
        if nested:
            raise ValueError(f"Unclosed block in {path}")
        return fields, i

    return block(0)[0]


def field_value(block, key):
    matches = [value for name, _, value in block if name == key]
    if len(matches) != 1:
        raise AssertionError(f"Expected one {key}, found {len(matches)}")
    return matches[0]


def walk(block):
    for name, op, value in block:
        yield name, op, value
        if isinstance(value, list):
            yield from walk(value)


def file_defs(subfolder):
    defs = {}
    for path in sorted((COMMON / subfolder).glob("*.txt")):
        for name, _, block in parse_script(path):
            if name in defs:
                raise AssertionError(f"Duplicate definition: {name}")
            defs[name] = block
    return defs


TRIGGERS = file_defs("scripted_triggers")
VALUES = file_defs("script_values")
CULTURES = {
    value.removeprefix("cu:")
    for key, _, value in walk(TRIGGERS["ocm_is_chinese_pop"])
    if key == "culture"
}
MIN_SHARE = Decimal(field_value(VALUES["ocm_required_population"], "multiply"))


@dataclass
class Country:
    counts: dict[str, int]
    tag: str = "SIA"
    tier: str = "kingdom"
    rank: str = "minor"
    primary: set[str] = field(default_factory=lambda: {"thai"})
    alive: bool = True
    is_player: bool = False
    revolution_origin: str | None = None
    central_government: bool = False
    subject_counts: dict[str, int] = field(default_factory=dict)

    def china(self):
        return self.tag == "CHI" or self.revolution_origin == "CHI" or self.central_government

    def eligible(self):
        total = sum(self.counts.values())
        required = int((total * MIN_SHARE).to_integral_value(rounding=ROUND_CEILING))
        return (self.alive and not self.china() and self.tier != "hegemony"
                and "han" not in self.primary and total > 0
                and sum(self.counts.get(c, 0) for c in CULTURES) >= required)


def settle_model(actor, countries, apply_culture):
    if not (actor.is_player and actor.china()):
        return 0
    confirmed = 0
    for country in countries:
        if country.eligible():
            apply_culture(country, "han")
            confirmed += "han" in country.primary
    return confirmed


class Logic(unittest.TestCase):
    def test_threshold(self):
        for count, eligible in [(0, False), (3900, False), (3999, False), (4000, True),
                                (4001, True), (5000, True), (10_000, True)]:
            with self.subTest(count=count):
                self.assertEqual(Country({"han": count, "thai": 10_000-count}).eligible(), eligible)
        self.assertFalse(Country({}).eligible())
        self.assertFalse(Country({"han": 1, "thai": 2}).eligible())
        self.assertTrue(Country({"han": 2, "thai": 3}).eligible())

    def test_four_culture_sum_only(self):
        cases = [
            ({"han": 10, "min": 10, "yue": 10, "hakka": 10}, True),
            ({"min": 20, "yue": 15, "hakka": 5}, True),
            ({"han": 20, "min": 10, "yue": 5, "hakka": 4}, False),
            ({"manchu": 40, "japanese": 20, "han": 39}, False),
        ]
        for groups, expected in cases:
            with self.subTest(groups=groups):
                self.assertEqual(Country({**groups, "thai": 100-sum(groups.values())}).eligible(), expected)

    def test_cheap_prefilter_cannot_exclude_valid_count_using_exact_shares(self):
        for groups in [(1000, 1000, 1000, 1000), (0, 2000, 1500, 500), (4000, 0, 0, 0)]:
            self.assertGreaterEqual(max(Decimal(count)/10_000 for count in groups), Decimal("0.09"))
        # The integer reference works above any plausible country population.
        self.assertTrue(Country({"han": 1_600_000_000, "thai": 2_400_000_000}).eligible())
        self.assertFalse(Country({"han": 1_599_999_999, "thai": 2_400_000_001}).eligible())

    def test_national_scope_excludes_subjects(self):
        country = Country({"han": 39, "thai": 61}, subject_counts={"hakka": 400})
        self.assertFalse(country.eligible())

    def test_target_flags_and_ranks(self):
        for flags, expectation in [
            ({"rank": "great_power"}, True),
            ({"rank": "unrecognized"}, True),
            ({"tier": "hegemony"}, False),
            ({"primary": {"thai", "han"}}, False),
            ({"tag": "CHI"}, False),
            ({"revolution_origin": "CHI"}, False),
            ({"central_government": True}, False),
            ({"alive": False}, False),
        ]:
            with self.subTest(flags=flags):
                self.assertEqual(Country({"hakka": 90, "thai": 10}, **flags).eligible(), expectation)

    def test_all_targets_and_confirmed_results(self):
        actor = Country({"han": 100}, tag="CHI", is_player=True)
        first = Country({"han": 40, "thai": 60}, primary={"thai", "shan"})
        second = Country({"min": 50, "thai": 50}, rank="great_power")
        subject = Country({"hakka": 45, "thai": 55}, tag="SUB", rank="subject")
        hegemon = Country({"han": 90, "thai": 10}, tier="hegemony")
        already = Country({"han": 90, "thai": 10}, primary={"han"})
        targets = [actor, first, second, subject, hegemon, already]

        def append(country, culture):
            country.primary.add(culture)

        self.assertEqual(settle_model(actor, targets, append), 3)
        self.assertEqual(first.primary, {"han", "thai", "shan"})
        self.assertEqual(first.counts, {"han": 40, "thai": 60})
        self.assertEqual(hegemon.primary, {"thai"})
        self.assertEqual(settle_model(actor, targets, append), 0)
        self.assertEqual(settle_model(actor, [Country({"han": 40, "thai": 60})], lambda *_: None), 0)

    def test_only_player_chinese_actors(self):
        for actor, expected in [
            (Country({}, tag="CHI", is_player=True), 1),
            (Country({}, revolution_origin="CHI", is_player=True), 1),
            (Country({}, central_government=True, is_player=True), 1),
            (Country({}, tag="CHI"), 0),
            (Country({}, is_player=True, primary={"thai", "han"}), 0),
        ]:
            target = Country({"yue": 40, "thai": 60})
            self.assertEqual(settle_model(actor, [target], lambda c, k: c.primary.add(k)), expected)


class Static(unittest.TestCase):
    def test_metadata_and_independence(self):
        meta = json.loads((MOD / ".metadata/metadata.json").read_text())
        self.assertEqual((meta["id"], meta["version"], meta["supported_game_version"]),
                         (MOD.name, "1.0.0", "1.15.2"))
        self.assertEqual(meta["relationships"], [])
        for path in MOD.rglob("*"):
            if path.is_dir():
                self.assertTrue(any(path.iterdir()), path)
            elif path.suffix in {".txt", ".yml", ".json"}:
                if path.is_relative_to(MOD / "docs"):
                    continue
                text = path.read_text(encoding="utf-8-sig")
                self.assertNotRegex(text, r"(?i)nan_?yang_?migration|nym_|replace_path|has_dlc_feature")
                if path.suffix == ".txt":
                    parse_script(path)

    def test_eligibility_wiring(self):
        self.assertEqual(CULTURES, {"han", "min", "yue", "hakka"})
        self.assertEqual(MIN_SHARE, Decimal("0.4"))
        self.assertEqual(VALUES["ocm_chinese_population"], [
            ("value", "=", "0"),
            ("every_scope_pop", "=", [
                ("limit", "=", [("ocm_is_chinese_pop", "=", "yes")]),
                ("add", "=", "total_size"),
            ]),
        ])
        self.assertEqual(VALUES["ocm_required_population"], [
            ("value", "=", "total_population"), ("multiply", "=", "0.4"), ("ceiling", "=", "yes"),
        ])
        target = field_value(TRIGGERS["ocm_is_eligible_target"], "trigger_if")
        cheap = field_value(target, "limit")
        self.assertIn(("is_country_alive", "=", "yes"), cheap)
        self.assertIn(("total_population", ">", "0"), cheap)
        excluded = field_value(cheap, "NOR")
        self.assertEqual({tuple(x) for x in excluded}, {
            ("ocm_is_china", "=", "yes"), ("country_tier", "=", "hegemony"),
            ("country_has_primary_culture", "=", "cu:han"),
        })
        self.assertIn(("ocm_chinese_population", ">=", "ocm_required_population"), list(walk(target)))
        prefilter = field_value(TRIGGERS["ocm_may_have_large_community"], "OR")
        self.assertTrue(all(key == "culture_percent_country" and ("value", ">=", "0.09") in entry
                            for key, _, entry in prefilter))
        self.assertEqual({field_value(entry, "target") for _, _, entry in prefilter}, {"cu:"+x for x in CULTURES})

    def test_journal_button_effect_and_events(self):
        journal = file_defs("journal_entries")["ocm_je_mobilization"]
        self.assertEqual(field_value(journal, "context"), "country")
        self.assertFalse({key for key, _, _ in journal} & {"outcome", "complete", "fail", "timeout"})
        button = file_defs("scripted_buttons")[field_value(journal, "scripted_button")]
        self.assertEqual(field_value(button, "ai_chance"), [("base", "=", "0")])
        self.assertFalse({key for key, _, _ in button} & {"cooldown", "cost", "autocomplete"})
        self.assertIn(("ocm_is_eligible_target", "=", "yes"), list(walk(field_value(button, "possible"))))
        self.assertEqual(field_value(button, "visible"), [("ocm_can_mobilize", "=", "yes")])
        callable_effect, _, _ = field_value(field_value(button, "effect"), "hidden_effect")[0]
        effect = field_value(file_defs("scripted_effects")[callable_effect], "if")
        self.assertEqual(field_value(effect, "limit"), [("ocm_can_mobilize", "=", "yes")])
        iterate = field_value(effect, "every_country")
        self.assertEqual([key for key, _, _ in iterate], ["limit", "add_primary_culture", "if"])
        self.assertEqual(field_value(iterate, "limit"), [("ocm_is_eligible_target", "=", "yes")])
        self.assertEqual(field_value(iterate, "add_primary_culture"), "cu:han")
        self.assertEqual(field_value(field_value(iterate, "if"), "limit"),
                         [("country_has_primary_culture", "=", "cu:han")])
        self.assertEqual([name for name, _, _ in effect],
                         ["limit", "save_scope_as", "set_variable", "every_country",
                          "save_scope_value_as", "if", "else", "remove_variable"])
        snapshots = field_value(effect, "save_scope_value_as")
        self.assertEqual(field_value(snapshots, "value"), "var:ocm_confirmed_count")
        self.assertIn(("var:ocm_confirmed_count", ">", "0"), list(walk(field_value(effect, "if"))))
        event_blocks = parse_script(MOD / "events/ocm_events.txt")
        events = {name: block for name, _, block in event_blocks if isinstance(block, list)}
        self.assertEqual({field_value(block, "id") for key, _, block in walk(effect)
                          if key == "trigger_event"}, events.keys())
        loc_refs = {"ocm_je_mobilization", "ocm_je_mobilization_reason"}
        loc_refs |= {value for key, _, value in walk(button)
                     if key in {"name", "desc", "text", "custom_tooltip"} and isinstance(value, str)}
        for event in events.values():
            option = field_value(event, "option")
            self.assertEqual([k for k, _, _ in option], ["name"])
            loc_refs |= {field_value(event, "title"), field_value(event, "desc"), field_value(option, "name")}
        for lang in ["english", "simp_chinese"]:
            raw = (MOD / f"localization/{lang}/ocm_l_{lang}.yml").read_bytes()
            self.assertTrue(raw.startswith(b"\xef\xbb\xbf"))
            header, *lines = raw.decode("utf-8-sig").splitlines()
            self.assertEqual(header, f"l_{lang}:")
            entries = {}
            for line in lines:
                match = re.fullmatch(r' (ocm_\w+):0 "((?:[^"\\]|\\[n"\\])*)"', line)
                self.assertIsNotNone(match, line)
                self.assertNotIn(match[1], entries)
                entries[match[1]] = match[2]
            self.assertEqual(entries.keys(), loc_refs)
            self.assertIn("SCOPE.GetValue('" + field_value(snapshots, "name") + "')", entries["ocm_success_desc"])

    def test_event_art(self):
        for _, _, block in parse_script(MOD / "events/ocm_events.txt"):
            if isinstance(block, list):
                path = MOD / field_value(field_value(block, "event_image"), "texture").strip('"')
                art = path.read_bytes()
                self.assertEqual(art[:4], b"DDS ")
                self.assertEqual(art[84:88], b"DXT1")
                self.assertEqual(unpack_from("<II", art, 12), (960, 1280))
                self.assertEqual(len(art), 128 + (1280//4)*(960//4)*8)


if __name__ == "__main__":
    unittest.main()

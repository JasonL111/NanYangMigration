"""Specification-level cases for the reform. No Jomini execution."""

from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import json
import unittest


@dataclass(frozen=True)
class Country:
    key: str = "qing"
    definition: str = "CHI"
    civil_war_origin: str | None = None
    central_government: bool = False
    han_is_primary: bool = True
    monarchy: bool = True
    player: bool = True
    alive: bool = True
    landowner_clout: Decimal | None = Decimal("0.20")


def can_enact(country, year):
    chinese = country.definition == "CHI" or country.civil_war_origin == "CHI" or country.central_government
    return (
        chinese and country.monarchy and country.player and country.alive
        and year >= 1861 and country.landowner_clout is not None and country.landowner_clout >= Decimal("0.20")
    )


@dataclass
class Campaign:
    enacted: bool = False
    pending_country: str | None = None
    active_country: str | None = None
    ends_in_year: int | None = None

    def submit(self, country, year):
        if self.enacted or self.pending_country is not None or not can_enact(country, year):
            return False
        self.pending_country = country.key
        return True

    def answer(self, country, year, approve, modifier_applied=True):
        if self.pending_country != country.key:
            return False
        self.pending_country = None
        if not approve or not can_enact(country, year) or self.enacted or not modifier_applied:
            return False
        self.enacted = True
        self.active_country = country.key
        self.ends_in_year = year + 20
        return True

    def active(self, country, year):
        return country.key == self.active_country and self.ends_in_year is not None and year < self.ends_in_year


class ReformRulesTests(unittest.TestCase):
    def test_chinese_monarchies_and_exclusions(self):
        qing = Country()
        cases = {
            "Qing": (qing, True),
            "civil war successor": (replace(qing, key="revolt", definition="REV", civil_war_origin="CHI"), True),
            "central government": (replace(qing, key="central", definition="BEI", central_government=True), True),
            "republic": (replace(qing, monarchy=False), False),
            "foreign monarchy with Han": (replace(qing, definition="SIK"), False),
            "AI Qing": (replace(qing, player=False), False),
            "inactive China": (replace(qing, alive=False), False),
        }
        for label, (country, expected) in cases.items():
            with self.subTest(country=label):
                self.assertEqual(can_enact(country, 1861), expected)

    def test_year_gate(self):
        for year, eligible in ((1836, False), (1860, False), (1861, True), (1870, True), (1900, True)):
            with self.subTest(year=year):
                self.assertEqual(can_enact(Country(), year), eligible)

    def test_effective_group_clout_boundary(self):
        cases = (("0", False), ("0.10", False), ("0.1999", False), ("0.20", True),
                 ("0.2001", True), ("0.40", True), ("0.80", True), (None, False))
        for clout, eligible in cases:
            with self.subTest(clout=clout):
                country = Country(landowner_clout=Decimal(clout) if clout is not None else None)
                self.assertEqual(can_enact(country, 1861), eligible)

    def test_open_petition_blocks_both_same_country_and_successor(self):
        campaign = Campaign()
        qing = Country()
        successor = Country(key="other", definition="REV", civil_war_origin="CHI")
        self.assertTrue(campaign.submit(qing, 1861))
        after_reload = Campaign(**json.loads(json.dumps(asdict(campaign))))
        for player in (qing, successor):
            self.assertFalse(after_reload.submit(player, 1861))
        self.assertFalse(after_reload.answer(successor, 1861, approve=True))
        self.assertEqual(after_reload.pending_country, qing.key)

    def test_defer_and_invalid_approval_leave_entitlement_unused(self):
        qing = Country()
        cases = ((qing, False, True), (replace(qing, monarchy=False), True, True),
                 (replace(qing, player=False), True, True),
                 (replace(qing, landowner_clout=Decimal("0.19")), True, True), (qing, True, False))
        for actor, approve, applied in cases:
            with self.subTest(actor=actor, approve=approve, applied=applied):
                campaign = Campaign()
                self.assertTrue(campaign.submit(qing, 1861))
                self.assertFalse(campaign.answer(actor, 1861, approve, applied))
                self.assertFalse(campaign.enacted)
                self.assertIsNone(campaign.active_country)
                self.assertTrue(campaign.submit(qing, 1861))

    def test_enact_applies_only_to_actor_once_even_after_expiry_and_reload(self):
        campaign = Campaign()
        qing = Country()
        successor = Country(key="other", definition="REV", civil_war_origin="CHI")
        self.assertTrue(campaign.submit(qing, 1861))
        self.assertTrue(campaign.answer(qing, 1861, approve=True))
        self.assertIsNone(campaign.pending_country)
        self.assertTrue(campaign.active(qing, 1880))
        self.assertFalse(campaign.active(successor, 1861))
        self.assertFalse(campaign.active(qing, 1881))
        self.assertFalse(campaign.answer(qing, 1861, approve=True))
        after_reload = Campaign(**json.loads(json.dumps(asdict(campaign))))
        for player in (qing, successor):
            self.assertFalse(after_reload.submit(player, 1900))


if __name__ == "__main__":
    unittest.main()

import unittest

from test_companies import SPECS


def eligible_country(definition, *, civil_war_origin=None, central_government=False, alive=True):
    return alive and (definition == "CHI" or civil_war_origin == "CHI" or central_government)


def eligible_size(company, states, headquarters=None):
    """Compute the design's level total from owned-state fixture rows."""
    spec = SPECS[company]
    if company == "shandong_agricultural_group":
        if headquarters != "STATE_SHANDONG":
            return False
        states = [state for state in states if state["region"] == headquarters]
    completed = sum(
        levels for state in states if state["owned"]
        for building, levels in state["levels"].items() if building in spec.buildings
    )
    return completed >= spec.levels


def province(region, levels, owned=True):
    return {"region": region, "owned": owned, "levels": levels}


def can_form(company, states, researched, *, slot_available):
    return slot_available and SPECS[company].technology in researched and eligible_size(company, states)


class DesignRuleTests(unittest.TestCase):
    def test_chinese_definition_and_successors(self):
        self.assertTrue(eligible_country("CHI"))  # Same definition under Qing or republican dynamic names.
        self.assertTrue(eligible_country("REV", civil_war_origin="CHI"))
        self.assertTrue(eligible_country("BEI", central_government=True))
        self.assertFalse(eligible_country("SIA"))  # Changing an overseas country's primary culture is irrelevant.
        self.assertFalse(eligible_country("CHI", alive=False))

    def test_huaxing_combines_levels_across_states(self):
        company = "huaxing_industries"
        owned = [
            province("STATE_ZHILI", {"tooling_workshop": 14, "university": 100}),
            province("STATE_SHANDONG", {"steel_mill": 15}),
        ]
        self.assertFalse(eligible_size(company, owned))
        self.assertFalse(eligible_size(
            company, owned + [province("STATE_MALAYA", {"power_plant": 100}, owned=False)],
        ))
        self.assertTrue(eligible_size(company, owned + [province("STATE_SHANXI", {"railway": 1})]))

    def test_shandong_does_not_count_foreign_split_or_other_owned_states(self):
        company = "shandong_agricultural_group"
        states = [province("STATE_SHANDONG", {"wheat_farm": 12, "millet_farm": 7}),
                  province("STATE_SHANDONG", {"wheat_farm": 30}, owned=False),
                  province("STATE_ZHILI", {"rice_farm": 80})]
        self.assertFalse(eligible_size(company, states, headquarters="STATE_SHANDONG"))
        states[0]["levels"]["millet_farm"] = 8
        self.assertTrue(eligible_size(company, states, headquarters="STATE_SHANDONG"))
        self.assertFalse(eligible_size(company, states, headquarters="STATE_ZHILI"))

    def test_cash_crops_include_vineyards_and_exclude_banana_and_grain(self):
        company = "fengzhi_trading_house"
        home = province("STATE_YUNNAN", {"tea_plantation": 12, "banana_plantation": 50, "rice_farm": 30})
        self.assertFalse(eligible_size(company, [home]))
        self.assertTrue(eligible_size(company, [home, province("STATE_SHANXI", {"vineyard": 8})]))

    def test_mining_counts_copper_but_excludes_oil_and_gold_fields(self):
        company = "chinese_mining_corporation"
        home = province("STATE_SHANXI", {"copper_mine": 18, "oil_rig": 20, "gold_field": 20})
        self.assertFalse(eligible_size(company, [home]))
        home["levels"]["gold_mine"] = 2
        self.assertTrue(eligible_size(company, [home]))

    def test_automotive_and_aircraft_share_building_with_distinct_tech_gates(self):
        states = [province("STATE_ZHILI", {"motor_industry": 9, "automotive_industry": 11})]
        self.assertTrue(eligible_size("shenzhou_motor_works", states))
        self.assertFalse(eligible_size("lingyun_aviation_works", states))
        self.assertEqual(SPECS["shenzhou_motor_works"].technology, "combustion_engine")
        self.assertEqual(SPECS["lingyun_aviation_works"].technology, "military_aviation")

    def test_technology_and_stock_company_slot_are_independent_requirements(self):
        company = "lingyun_aviation_works"
        states = [province("STATE_ZHILI", {"automotive_industry": 20})]
        self.assertFalse(can_form(company, states, {"combustion_engine"}, slot_available=True))
        self.assertFalse(can_form(company, states, {"military_aviation"}, slot_available=False))
        self.assertTrue(can_form(company, states, {"military_aviation"}, slot_available=True))


if __name__ == "__main__":
    unittest.main()

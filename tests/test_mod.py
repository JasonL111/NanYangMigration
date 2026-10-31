import copy
import hashlib
import json
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from build_mod import CULTURES, MATRIX, TARGETS, REGIONS, CELLS, apportion
from script_harness import Harness, Country, State, Pop, parse, fields
MOD = ROOT / 'nanyang_migration'

def world(uses=0, available=10_000_000, split=1, religion='confucian'):
    h = Harness(MOD)
    h.globals['nym_uses'] = uses
    source = State('BEIJING', h.country)
    h.states.append(source)
    h.pops = [Pop(source, c, available, religion) for c in CULTURES]
    foreign = Country('cd:GBR', False)
    for r, states in REGIONS.items():
        for i in range(split):
            h.states.append(State(states[0], foreign if i == 0 else Country('cd:FRA', False)))
    return h

class Files(unittest.TestCase):
    def test_metadata(self):
        d = json.loads((MOD/'.metadata/metadata.json').read_text())
        self.assertEqual(d['version'], '1.0.2')
        self.assertEqual(d['supported_game_version'], '1.13.11')

    def test_all_scripts_parse_and_no_empty_files(self):
        for f in MOD.rglob('*'):
            if f.is_file(): self.assertGreater(f.stat().st_size, 0, str(f))
            if f.is_dir(): self.assertTrue(list(f.iterdir()), str(f))
            if f.suffix == '.txt' and f.relative_to(MOD).parts[0] in ('common', 'events'):
                parse(f.read_text(encoding='utf-8-sig'))

    def test_localizations(self):
        keys = []
        for lang in ('english', 'simp_chinese'):
            b = (MOD/f'localization/{lang}/nanyang_l_{lang}.yml').read_bytes()
            self.assertTrue(b.startswith(b'\xef\xbb\xbf'))
            s = b.decode('utf-8-sig')
            self.assertTrue(s.startswith('l_'+lang+':'))
            entries = re.findall(r'^ ([\w.]+):0 "(.*)"$', s, re.M)
            self.assertEqual(len(entries), len(set(k for k, _ in entries)))
            keys.append(set(k for k, _ in entries))
        self.assertEqual(*keys)
        required = {'je_nanyang_migration', 'je_nanyang_migration_reason'}
        for f in MOD.rglob('*.txt'):
            required.update(re.findall(r'\b(?:name|desc|title|text)\s*=\s*(nym_\w+)\b', f.read_text()))
        # Numeric variable names are not localisation references.
        required = {x for x in required if x not in {'nym_uses','nym_last','nym_last_target','nym_requested','nym_actual','nym_cell_unassigned','nym_states_left','nym_cell_actual','nym_quota','nym_delta','nym_before','nym_available','nym_origin','nym_amount','nym_cooldown','nym_source_count','nym_source_size','nym_source_people','nym_transfer_calls','nym_transfer_requested'} and not x.startswith(('nym_count_', 'nym_actual_'))}
        self.assertLessEqual(required, keys[0])

    def test_definition_references(self):
        h = Harness(MOD)
        journal = fields(h.defs['je_nanyang_migration'])
        self.assertIn(journal['scripted_button'], h.defs)
        text = '\n'.join(f.read_text() for f in (MOD/'common').rglob('*.txt'))
        # All concrete nym identifiers used as call keys or arithmetic values exist.
        definitions = set(h.defs)
        calls = set(re.findall(r'(?<!:)\b(nym_\w+)\s*=\s*(?:yes|no|\{)', text))
        values = set(re.findall(r'\b(?:value|AMOUNT)\s*=\s*(nym_\w+)\b', text))
        self.assertLessEqual(calls | values, definitions)
        events = parse((MOD/'events/nanyang_events.txt').read_text())
        ids = {k for k,_,_ in events}
        self.assertLessEqual(set(re.findall(r'id\s*=\s*(nanyang_migration\.\d+)', text)), ids)
        self.assertNotIn('$', text.replace('$REGION$', '').replace('$CULTURE$', '').replace('$AMOUNT$', ''))

    def test_versioned_identifiers(self):
        evidence = json.loads((MOD/'docs/reference_ids.json').read_text())
        self.assertEqual(evidence['version'], '1.13.11 (Matcha)')
        self.assertLessEqual(set(CULTURES), set(evidence['cultures']))
        self.assertIn('CHI', evidence['countries'])
        for names in REGIONS.values():
            self.assertLessEqual({'STATE_'+s for s in names}, set(evidence['states']))
        all_states = [s for names in REGIONS.values() for s in names]
        self.assertEqual(len(all_states), len(set(all_states)))
        self.assertIn('NAKHON_RATCHASIMA', REGIONS['siam'])

    def test_no_fake_population_creation(self):
        text = '\n'.join(f.read_text() for f in MOD.rglob('*.txt'))
        for forbidden in ('create_pop', 'kill_population', 'add_pop', 'set_pop_culture', 'set_pop_religion', 'create_mass_migration'):
            self.assertNotRegex(text, r'\b'+forbidden+r'\s*=')
        self.assertIn('move_partial_pop =', text)
        self.assertIn('population = scope:nym_amount', text)
        self.assertNotIn('workforce', re.sub(r'#.*', '', text).lower())

    def test_native_timer_and_permanent_journal(self):
        h = Harness(MOD)
        j = fields(h.defs['je_nanyang_migration'])
        self.assertFalse(h.condition(j['complete'], h.country))
        self.assertFalse(h.condition(j['fail'], h.country))
        text = (MOD/'common/scripted_effects/nanyang_effects.txt').read_text()
        self.assertIn('name = nym_cooldown value = yes years = 5', text)
        self.assertNotIn('days = 1825', text)
        self.assertNotIn('on_weekly_pulse', text)

class Mathematics(unittest.TestCase):
    def test_jomini_bounds_semantics(self):
        # Vanilla 00_diplomacy_values.txt clamps to [0.01, 0.05] with
        # min = 0.01, max = 0.05; these are bounds, not Python min()/max().
        h = Harness(MOD)
        self.assertEqual(h.formula(parse('value = 100 max = 7'), h.country), 7)
        self.assertEqual(h.formula(parse('value = -2 min = 0'), h.country), 0)
        self.assertEqual(h.formula(parse('value = 8 min = 0'), h.country), 8)
        self.assertEqual(h.formula(parse('value = 100 max = 50 max = 20'), h.country), 20)

    def test_matrix(self):
        self.assertEqual([sum(row[i] for row in MATRIX.values()) for i in range(4)], [45,30,15,10])
        self.assertEqual([sum(row) for row in MATRIX.values()], [35,25,20,12,5,3])
        self.assertEqual(sum(w for _,_,w in CELLS), 100)

    def test_growth_from_actual_script_values(self):
        from decimal import Decimal, ROUND_HALF_UP
        h = Harness(MOD)
        for uses in range(20):
            expected = min(int((Decimal(2_000_000)*Decimal('1.25')**uses).quantize(Decimal(1), rounding=ROUND_HALF_UP)), 5_000_000)
            h.globals['nym_uses'] = uses
            self.assertEqual(h.resolve('nym_target', h.country), expected)
        self.assertEqual(TARGETS, [2000000,2500000,3125000,3906250,4882813,5000000])

    def test_rounding_from_emitted_values(self):
        h = Harness(MOD)
        for uses, target in enumerate(TARGETS):
            h.globals['nym_uses'] = uses
            amounts = [h.resolve('nym_plan_'+r+'_'+c, h.country) for r,c,_ in CELLS]
            self.assertEqual(sum(amounts), target)
            self.assertEqual(amounts, apportion(target))
            for amount, (_,_,weight) in zip(amounts, CELLS):
                self.assertLess(abs(amount-target*weight/100), 1)

class Execution(unittest.TestCase):
    def test_diagnostic_counters(self):
        h = world()
        h.click()
        self.assertEqual(h.country.vars['nym_source_count'], 4)
        self.assertEqual(h.country.vars['nym_source_people'], 40_000_000)
        self.assertEqual(h.country.vars['nym_transfer_requested'], 2_000_000)
        self.assertEqual(h.country.vars['nym_transfer_calls'], len(CELLS))
        h = world()
        h.states = h.states[:1]
        h.click()
        self.assertEqual(h.country.vars['nym_source_count'], 4)
        self.assertEqual(h.country.vars['nym_transfer_calls'], 0)
        self.assertEqual(h.country.vars['nym_transfer_requested'], 0)

    def test_full_transfer_and_matrix_all_six_levels(self):
        for uses,target in enumerate(TARGETS):
            with self.subTest(uses=uses):
                h = world(uses)
                total = sum(p.size for p in h.pops)
                before = h.population(h.states[0])
                h.click()
                self.assertEqual(h.globals['nym_last'], target)
                self.assertEqual(before-h.population(h.states[0]), target)
                self.assertEqual(sum(p.size for p in h.pops), total)
                self.assertEqual(h.moved, target)
                for (r,c,_), expected in zip(CELLS, apportion(target)):
                    self.assertEqual(h.globals['nym_actual_'+r+'_'+c], expected)
                self.assertEqual(h.events, ['nanyang_migration.1'])

    def test_split_states_equal_and_integer_remainders(self):
        h = world(uses=4, split=3)
        h.click()
        for r,c,_ in CELLS:
            amounts = [sum(p.size for p in h.pops if p.state is s and p.culture == c) for s in h.states[1:] if s.region == REGIONS[r][0]]
            self.assertLessEqual(max(amounts)-min(amounts), 1)
        self.assertEqual(h.moved, TARGETS[4])

    def test_missing_region_no_redistribution(self):
        h = world()
        h.states = [s for s in h.states if s.region not in REGIONS['siam']]
        h.click()
        self.assertEqual(h.moved, 1_600_000)
        self.assertEqual(h.globals['nym_actual_siam_min'], 0)

    def test_culture_shortage_no_substitution(self):
        h = world()
        h.pops = [p for p in h.pops if p.culture != 'min']
        h.click()
        self.assertEqual(h.moved, 1_100_000)
        self.assertEqual(h.globals['nym_uses'], 1)
        self.assertEqual(h.durations['nym_cooldown'], ('years', 5))

    def test_limited_source_never_negative(self):
        h = world(available=133)
        h.click()
        self.assertEqual(h.moved, 532)
        self.assertTrue(all(p.size >= 0 for p in h.pops))
        self.assertEqual(h.globals['nym_last'], 532)

    def test_zero_no_use_or_cooldown(self):
        for reason in ('pops', 'destinations'):
            h = world()
            if reason == 'pops': h.pops = []
            else: h.states = h.states[:1]
            h.click()
            self.assertEqual(h.globals['nym_uses'], 0)
            self.assertNotIn('nym_cooldown', h.globals)
            self.assertEqual(h.events, ['nanyang_migration.2'])

    def test_cooldown_reload_successor_and_resume(self):
        h = world()
        h.click()
        h.globals = copy.deepcopy(h.globals)  # simulate saving persistent scalar state
        h.country = Country()  # successor using the same CHI country definition
        h.click()
        self.assertEqual(h.moved, 2_000_000)
        del h.globals['nym_cooldown']  # emulate native variable expiry, not a test of game time
        source = State('BEIJING', h.country)
        h.states.append(source)
        h.pops += [Pop(source, c, 10_000_000) for c in CULTURES]
        h.click()
        self.assertEqual(h.globals['nym_last'], 2_500_000)
        self.assertEqual(h.globals['nym_uses'], 2)

    def test_source_region_unrestricted(self):
        h = world()
        h.states[0].region = 'ALASKA'
        h.click()
        self.assertEqual(h.moved, 2_000_000)

    def test_religion_preserved(self):
        h = world(religion='protestant')
        h.click()
        self.assertTrue(all(p.religion == 'protestant' for p in h.pops))

    def test_ai_disabled(self):
        h = world()
        h.country.player = False
        h.click()
        self.assertEqual(h.moved, 0)
        self.assertEqual(h.resolve('0', h.country), 0)

    def test_destination_ownership_irrelevant(self):
        h = world()
        for s in h.states[1:]: s.owner = Country('cd:USA', False)
        h.click()
        self.assertEqual(h.moved, 2_000_000)

    def test_same_state_and_preexisting_arrival_budget(self):
        h = world(available=100)
        # Player-owned destinations are also valid origins, with preexisting pops.
        for s in h.states[1:]:
            s.owner = h.country
            h.pops.append(Pop(s, 'min', 15))
        initial = sum(p.size for p in h.pops)
        h.click()
        self.assertLessEqual(h.moved, initial)
        self.assertEqual(sum(p.size for p in h.pops), initial)
        self.assertTrue(all(a is not b for a,b,_,_ in h.transfers))
        self.assertTrue(all(p.size >= 0 for p in h.pops))

    def test_failure_preserves_last_success(self):
        h = world()
        h.click()
        del h.globals['nym_cooldown']
        h.pops = []
        h.click()
        self.assertEqual(h.globals['nym_uses'], 1)
        self.assertEqual(h.globals['nym_last'], 2_000_000)
        self.assertNotIn('nym_cooldown', h.globals)

if __name__ == '__main__':
    unittest.main(verbosity=2)

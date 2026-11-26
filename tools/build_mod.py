"""Generate the distributable native-script mod. Python is a development tool only."""
from pathlib import Path
from fractions import Fraction
import json

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'nanyang_migration'
HARBOR_TEXTURE = 'gfx/event_pictures/nanyang_harbor.dds'
VERSION = '1.1.3'
GAME_VERSION = '1.15.2'
INITIAL_TARGET = 200_000
MAX_TARGET = 500_000
GROWTH_PERCENT = 25
COOLDOWN_YEARS = 3
CULTURES = ['min', 'yue', 'hakka', 'han']
MATRIX = {
    'malaya': [12, 10, 7, 6],
    'east_indies': [13, 4, 6, 2],
    'siam': [14, 3, 1, 2],
    'indochina': [2, 9, 1, 0],
    'philippines': [4, 1, 0, 0],
    'burma': [0, 3, 0, 0],
}
REGIONS = {
    'malaya': ['MALAYA'],
    'east_indies': ['ACEH', 'NORTH_SUMATRA', 'SOUTH_SUMATRA', 'WEST_JAVA',
                    'CENTRAL_JAVA', 'EAST_JAVA', 'WEST_BORNEO', 'EAST_BORNEO',
                    'CELEBES', 'MOLUCCAS', 'SUNDA_ISLANDS', 'WESTERN_NEW_GUINEA'],
    'siam': ['BANGKOK', 'CHIANG_MAI', 'NAKHON_RATCHASIMA'],
    'indochina': ['TONKIN', 'ANNAM', 'MEKONG', 'CAMBODIA', 'LAOS'],
    'philippines': ['LUZON', 'VISAYAS', 'MINDANAO'],
    'burma': ['ARAKAN', 'PEGU', 'MANDALAY', 'KACHIN', 'SHAN_STATES', 'TENASSERIM'],
}
CELLS = [(r, c, w) for r, row in MATRIX.items() for c, w in zip(CULTURES, row) if w]


def target_schedule():
    """Grow the exact base, rounding only the quota issued for each expedition."""
    exact = Fraction(INITIAL_TARGET)
    multiplier = Fraction(100 + GROWTH_PERCENT, 100)
    amounts = []
    while (rounded := int(exact + Fraction(1, 2))) < MAX_TARGET:
        amounts.append(rounded)
        exact *= multiplier
    return amounts + [MAX_TARGET]


TARGETS = target_schedule()


def apportion(total):
    """Hamilton: largest remainders, stable row-major tie break."""
    amounts = [total * w // 100 for _, _, w in CELLS]
    order = sorted(range(len(CELLS)), key=lambda i: (-(total * CELLS[i][2] % 100), i))
    for i in order[:total - sum(amounts)]:
        amounts[i] += 1
    return amounts

def write(path, contents, bom=False):
    dest = MOD / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(contents.strip() + '\n', encoding='utf-8-sig' if bom else 'utf-8')

def table_value(name, nums):
    out = f'{name} = {{\n    value = {nums[-1]}\n'
    for i, value in enumerate(nums[:-1]):
        out += ('    if' if i == 0 else '    else_if') + f' = {{ limit = {{ nym_uses = {i} }} value = {value} }}\n'
    return out + '}\n'

def main():
    if not (MOD / HARBOR_TEXTURE).is_file():
        raise FileNotFoundError(f'Missing event illustration: {HARBOR_TEXTURE}')
    write('.metadata/metadata.json', json.dumps({
        'name': '下南洋 · Nanyang Migration', 'id': 'nanyang_migration',
        'version': VERSION, 'supported_game_version': GAME_VERSION,
        'short_description': 'Player-organized Chinese migration to Southeast Asian states.',
        'tags': ['Gameplay', 'Historical'],
        'relationships': [], 'game_custom_data': {'multiplayer_synchronized': True},
    }, ensure_ascii=False, indent=2))
    triggers = '''# Country eligibility follows CHI definitions, civil-war origin and vanilla central-government scope.
nym_eligible = {
    is_player = yes
    OR = {
        country_definition = cd:CHI
        AND = {
            exists = civil_war_origin_country
            civil_war_origin_country = { country_definition = cd:CHI }
        }
        global_var:chinese_central_government ?= this
    }
}
nym_culture = {
    OR = { culture = cu:min culture = cu:yue culture = cu:hakka culture = cu:han }
}
'''
    for name, condition in (
        ('nym_culture_matches', lambda culture: f'culture = cu:{culture}'),
        ('nym_culture_has_receipt', lambda culture: f'has_variable = nym_received_{culture}'),
    ):
        triggers += f'\n{name} = {{\n    OR = {{\n'
        for index, culture in enumerate(CULTURES, 1):
            triggers += (f'        AND = {{ {condition(culture)} '
                         f'scope:nym_country = {{ var:nym_culture_index = {index} }} }}\n')
        triggers += '    }\n}\n'
    write('common/scripted_triggers/nanyang_triggers.txt', triggers)
    values = '''# The design budgets use persons. Native move units require the engine probe.
nym_uses = {
    value = 0
    if = { limit = { has_global_variable = nym_uses } value = global_var:nym_uses }
}
nym_last = {
    value = 0
    if = { limit = { has_global_variable = nym_last } value = global_var:nym_last }
}
nym_last_target = {
    value = 0
    if = { limit = { has_global_variable = nym_last_target } value = global_var:nym_last_target }
}
'''
    values += table_value('nym_target', TARGETS)
    values += table_value('nym_following_target', TARGETS[1:] + [MAX_TARGET])
    for i, (r, c, _) in enumerate(CELLS):
        values += table_value(f'nym_plan_{r}_{c}', [apportion(t)[i] for t in TARGETS])
    values += '''
# POP scope: read its live size and cap it against the country's destination quota.
nym_take = {
    value = total_size
    max = scope:nym_country.var:nym_quota
    floor = yes
}
nym_state_share = {
    value = var:nym_cell_unassigned
    divide = var:nym_states_left
    floor = yes
}
# Iterate actual POP objects. Avoid relying on the state's aggregate cache.
nym_live_population = {
    value = 0
    every_scope_pop = {
        limit = { nym_culture_matches = yes }
        add = total_size
    }
}
nym_source_delta = {
    value = var:nym_source_before
    subtract = scope:nym_origin_state.nym_live_population
}
nym_destination_delta = {
    value = scope:nym_destination.nym_live_population
    subtract = var:nym_destination_before
}
'''
    write('common/script_values/nanyang_values.txt', values)
    write('common/journal_entries/nanyang_journal.txt', '''
je_nanyang_migration = {
    group = je_group_foreign_affairs
    context = country
    should_be_pinned_by_default_uninvolved_or_context = yes
    transferable = no
    can_revolution_inherit = yes
    is_shown_when_inactive = { nym_eligible = yes }
    possible = { nym_eligible = yes }
    # Permanent: no outcome blocks and no timeout.
    scripted_button = nym_organize
}
''')
    write('common/scripted_buttons/nanyang_buttons.txt', '''
nym_organize = {
    name = nym_organize_name
    desc = nym_organize_desc
    visible = { nym_eligible = yes }
    possible = {
        nym_eligible = yes
        custom_tooltip = {
            text = nym_pending_tt
            NOT = { has_global_variable = nym_pending }
        }
        custom_tooltip = {
            text = nym_cooldown_tt
            NOT = { has_global_variable = nym_cooldown }
        }
    }
    ai_chance = { base = 0 }
    effect = {
        # Timed persistent variable rather than unconditional button cooldown:
        # zero-move attempts must not consume cooldown; successor countries share it.
        if = {
            limit = {
                nym_eligible = yes
                NOT = { has_global_variable = nym_cooldown }
                NOT = { has_global_variable = nym_pending }
            }
            hidden_effect = { nym_execute = yes }
            custom_tooltip = nym_attempt_tt
        }
    }
}
''')
    effects = '''# One button execution, held under a save-wide lock through verification.
nym_execute = {
    save_scope_as = nym_country
    set_global_variable = { name = nym_pending value = yes }
    if = {
        limit = { NOT = { has_global_variable = nym_uses } }
        set_global_variable = { name = nym_uses value = 0 }
    }
    set_variable = { name = nym_requested value = nym_target }
    set_variable = { name = nym_actual value = 0 }
    set_variable = { name = nym_source_count value = 0 }
    set_variable = { name = nym_source_people value = 0 }
    set_variable = { name = nym_transfer_calls value = 0 }
    set_variable = { name = nym_transfer_requested value = 0 }
    set_variable = { name = nym_cells_started value = 0 }
    set_variable = { name = nym_positive_shares value = 0 }
    set_variable = { name = nym_source_matches value = 0 }
    set_variable = { name = nym_culture_candidates value = 0 }
    set_variable = { name = nym_culture_index value = 0 }
    # A prior spent/aborted attempt must not leave receipt marks in owned states.
    every_scope_state = { nym_clear_receipts = yes }
    set_variable = { name = nym_last_request value = 0 }
    set_variable = { name = nym_source_delta value = 0 }
    set_variable = { name = nym_destination_delta value = 0 }

    # Initial census for the report. The game rejects variables on POP scope.
    every_scope_pop = {
        limit = { nym_culture = yes total_size >= 1 }
        save_scope_value_as = { name = nym_source_size value = total_size }
        scope:nym_country = {
            change_variable = { name = nym_source_count add = 1 }
            change_variable = { name = nym_source_people add = scope:nym_source_size }
        }
    }
'''
    for region in REGIONS:
        effects += f'''    set_variable = {{ name = nym_states_seen value = 0 }}
    set_variable = nym_counting_states
    nym_visit_{region} = yes
    remove_variable = nym_counting_states
    set_variable = {{ name = nym_count_{region} value = var:nym_states_seen }}
'''
    for region, culture, _ in CELLS:
        record = f'nym_actual_{region}_{culture}'
        effects += f'''    set_global_variable = {{ name = {record} value = 0 }}
    if = {{
        limit = {{
            NOT = {{ has_variable = nym_transfer_halted }}
            var:nym_source_count >= 1
            var:nym_count_{region} >= 1
            nym_plan_{region}_{culture} >= 1
        }}
        change_variable = {{ name = nym_cells_started add = 1 }}
        set_variable = {{ name = nym_culture_index value = {CULTURES.index(culture) + 1} }}
        set_variable = {{ name = nym_cell_unassigned value = nym_plan_{region}_{culture} }}
        set_variable = {{ name = nym_states_left value = var:nym_count_{region} }}
        set_variable = {{ name = nym_cell_actual value = 0 }}
        nym_visit_{region} = yes
        set_global_variable = {{ name = {record} value = var:nym_cell_actual }}
    }}
'''
    effects += '''    every_scope_state = { nym_clear_receipts = yes }
    if = {
        limit = { has_variable = nym_transfer_halted }
        remove_variable = nym_transfer_halted
        if = {
            limit = { var:nym_transfer_calls >= 1 }
            # Keep the lock after an unconfirmed native call, even if it was a no-op.
            trigger_event = { id = nanyang_migration.3 }
        }
        else = {
            remove_global_variable = nym_pending
            trigger_event = { id = nanyang_migration.2 }
        }
    }
    else_if = {
        limit = { var:nym_actual > 0 }
        set_global_variable = { name = nym_last value = var:nym_actual }
        set_global_variable = { name = nym_last_target value = var:nym_requested }
        change_global_variable = { name = nym_uses add = 1 }
        set_global_variable = { name = nym_cooldown value = yes years = @COOLDOWN_YEARS@ }
        remove_global_variable = nym_pending
        trigger_event = { id = nanyang_migration.1 }
    }
    else = {
        remove_global_variable = nym_pending
        trigger_event = { id = nanyang_migration.2 }
    }
}

# On a live State in a design region, count it or give it its share of the cell.
nym_visit_destination = {
    if = {
        limit = { scope:nym_country = { has_variable = nym_counting_states } }
        scope:nym_country = { change_variable = { name = nym_states_seen add = 1 } }
    }
    else_if = {
        limit = {
            scope:nym_country = {
                NOT = { has_variable = nym_transfer_halted }
                var:nym_states_left >= 1
            }
        }
        save_scope_as = nym_destination
        scope:nym_country = {
            set_variable = { name = nym_quota value = nym_state_share }
            change_variable = { name = nym_cell_unassigned subtract = var:nym_quota }
            change_variable = { name = nym_states_left subtract = 1 }
            if = {
                limit = { var:nym_quota >= 1 }
                change_variable = { name = nym_positive_shares add = 1 }
                nym_find_sources = yes
            }
        }
    }
}

# Country scope. Scope ownership comes from the country's actual State iterator.
nym_find_sources = {
    every_scope_state = {
        limit = { NOT = { this = scope:nym_destination } }
        if = {
            limit = {
                scope:nym_country = {
                    NOT = { has_variable = nym_transfer_halted }
                    var:nym_quota >= 1
                }
            }
            save_scope_as = nym_origin_state
            every_scope_pop = {
                limit = { nym_culture_matches = yes total_size >= 1 }
                if = {
                    limit = {
                        scope:nym_country = {
                            NOT = { has_variable = nym_transfer_halted }
                            var:nym_quota >= 1
                        }
                    }
                    scope:nym_country = { change_variable = { name = nym_culture_candidates add = 1 } }
                    # After arrivals, the state cannot distinguish old and newly
                    # merged POPs. Stop using it as a donor for this culture.
                    if = {
                        limit = { scope:nym_origin_state = { nym_culture_has_receipt = no } }
                        nym_transfer = yes
                    }
                }
            }
        }
    }
}

# POP scope on entry. After the native effect use only the saved country and states.
nym_transfer = {
    scope:nym_country = { change_variable = { name = nym_source_matches add = 1 } }
    save_scope_value_as = { name = nym_amount value = nym_take }
    if = {
        limit = { scope:nym_amount >= 1 }
        # Mark and verify the actual destination before any native mutation.
        scope:nym_destination = { nym_mark_receipt = yes }
        if = {
            limit = { scope:nym_destination = { nym_culture_has_receipt = yes } }
            nym_move_and_verify = yes
        }
        else = { scope:nym_country = { set_variable = nym_transfer_halted } }
    }
}

nym_move_and_verify = {
    scope:nym_country = {
        set_variable = { name = nym_source_before value = scope:nym_origin_state.nym_live_population }
        set_variable = { name = nym_destination_before value = scope:nym_destination.nym_live_population }
        set_variable = { name = nym_last_request value = scope:nym_amount }
        change_variable = { name = nym_transfer_calls add = 1 }
        change_variable = { name = nym_transfer_requested add = scope:nym_amount }
    }
    move_partial_pop = { state = scope:nym_destination population = scope:nym_amount }
    scope:nym_country = {
        set_variable = { name = nym_source_delta value = nym_source_delta }
        set_variable = { name = nym_destination_delta value = nym_destination_delta }
        if = {
            limit = {
                var:nym_source_delta > 0
                var:nym_source_delta = var:nym_destination_delta
                var:nym_destination_delta <= var:nym_last_request
            }
            change_variable = { name = nym_actual add = var:nym_destination_delta }
            change_variable = { name = nym_cell_actual add = var:nym_destination_delta }
            change_variable = { name = nym_quota subtract = var:nym_destination_delta }
        }
        else = { set_variable = nym_transfer_halted }
    }
}
'''
    # Use literal scopes and native iterators for both passes. The POP scopes
    # discovered by the engine are never recovered from a script-maintained list.
    for region, states in REGIONS.items():
        effects += f'\nnym_visit_{region} = {{\n'
        for state in states:
            effects += f'''    s:STATE_{state} ?= {{
        every_scope_state = {{
            limit = {{ exists = owner }}
            nym_visit_destination = yes
        }}
    }}
'''
        effects += '}\n'
    effects += '\nnym_mark_receipt = {\n'
    for index, culture in enumerate(CULTURES, 1):
        effects += f'''    if = {{
        limit = {{ scope:nym_country = {{ var:nym_culture_index = {index} }} }}
        set_variable = {{ name = nym_received_{culture} value = yes days = 1 }}
    }}
'''
    effects += '}\n\nnym_clear_receipts = {\n'
    for culture in CULTURES:
        effects += f'''    if = {{
        limit = {{ has_variable = nym_received_{culture} }}
        remove_variable = nym_received_{culture}
    }}
'''
    effects += '}\n'
    write('common/scripted_effects/nanyang_effects.txt', effects.replace('@COOLDOWN_YEARS@', str(COOLDOWN_YEARS)))
    events = 'namespace = nanyang_migration\n'
    for event_id, outcome in enumerate(('success', 'failure', 'pending'), 1):
        events += f'''nanyang_migration.{event_id} = {{
    type = country_event
    title = nym_{outcome}_title
    desc = nym_{outcome}_desc
    is_popup = yes
    event_image = {{ texture = "{HARBOR_TEXTURE}" }}
    option = {{ name = nym_ack }}
}}
'''
    write('events/nanyang_events.txt', events)
    def shown(name):
        return f"[GetPlayer.MakeScope.ScriptValue('{name}')|0]"

    current = shown('nym_target')
    following = shown('nym_following_target')
    departures = shown('nym_uses')
    previous_plan = shown('nym_last_target')
    previous_arrivals = shown('nym_last')
    zh = {
        'je_nanyang_migration': '下南洋',
        'je_nanyang_migration_reason': (
            '早有乡民自闽粤沿海扬帆，赴南洋谋生。如今官府可召集愿意远行的人家，'
            '为他们安排航程，到异乡安家。\\n\\n'
            f'已办航次：{departures}　待发人数：{current}\\n'
            f'上次计划：{previous_plan} 人　上次抵达：{previous_arrivals} 人\\n'
            f'本次顺利启航后，下次可筹办 {following} 人。'
        ),
        'nym_organize_name': '组织下南洋',
        'nym_organize_desc': (
            f'筹办一次赴南洋的航程，计划从本国各州招募 {current} 人。\\n\\n'
            '闽人占45%，粤人占30%，客家人占15%，汉人占10%。\\n'
            '马来亚及新加坡接收35%，荷属东印度25%，暹罗20%，印度支那12%，'
            '菲律宾5%，缅甸3%。\\n\\n'
            f'首航计划 {INITIAL_TARGET:,} 人。每次成功后，下一航次的计划人数增加 {GROWTH_PERCENT}%，'
            f'最多 {MAX_TARGET:,} 人。两次成功航次之间须休整 {COOLDOWN_YEARS} 个游戏年。'
        ),
        'nym_cooldown_tt': '船队的休整期已结束。',
        'nym_pending_tt': '上次航程尚未结报，暂不能再派船队。',
        'nym_attempt_tt': '派船将应募人家送往南洋。实际抵达人数将在航程结束后公布。',
        'nym_success_title': '南洋的新家园',
        'nym_success_desc': (
            '满载行囊的船队已抵达南洋。移民们在港口登岸，准备在当地谋生、安家。\\n\\n'
            f'本次计划 {previous_plan} 人，实际抵达 {previous_arrivals} 人。\\n'
            f'下一航次可筹办 {current} 人，船队需休整 {COOLDOWN_YEARS} 个游戏年。'
        ),
        'nym_failure_title': '航程未能启行',
        'nym_failure_desc': '这趟航程未能成行，本次没有派遣移民。待条件合适，便可再次筹办。',
        'nym_pending_title': '航报未至',
        'nym_pending_desc': (
            '各港的回报尚未齐备，官府暂缓派出下一支船队。'
            '如需重新筹办这次航程，请载入启航前的存档。'
        ),
        'nym_ack': '知悉',
    }
    en = {
        'je_nanyang_migration': 'Nanyang Migration',
        'je_nanyang_migration_reason': (
            'For generations, families have sailed from the ports of southern China to seek '
            'a living in Nanyang. The government can now arrange passage for those who wish '
            'to make a home across the sea.\\n\\n'
            f'Expeditions completed: {departures}. Current plan: {current} people.\\n'
            f'Last expedition: {previous_plan} planned, {previous_arrivals} arrived.\\n'
            f'If this expedition succeeds, the next can carry {following} people.'
        ),
        'nym_organize_name': 'Organize Nanyang Migration',
        'nym_organize_desc': (
            f'Arrange passage to Nanyang for up to {current} people from your states.\\n\\n'
            'The expedition is planned for Min 45%, Yue 30%, Hakka 15%, and Han 10%.\\n'
            'Destinations are Malaya and Singapore 35%, the Dutch East Indies 25%, Siam 20%, '
            'Indochina 12%, the Philippines 5%, and Burma 3%.\\n\\n'
            f'The first expedition plans for {INITIAL_TARGET:,} people. Each success increases the next '
            f'plan by {GROWTH_PERCENT}% up to {MAX_TARGET:,}. The fleet rests for {COOLDOWN_YEARS} in-game years after each success.'
        ),
        'nym_cooldown_tt': 'The fleet has finished refitting.',
        'nym_pending_tt': 'Reports from the last voyage must come in before another fleet can depart.',
        'nym_attempt_tt': 'Send the settlers to Nanyang. The arrival report will record how many reached their destinations.',
        'nym_success_title': 'New Homes in Nanyang',
        'nym_success_desc': (
            'The fleet has reached Nanyang. Families are stepping ashore with their belongings, '
            'ready to make a living in their new homes.\\n\\n'
            f'The expedition planned for {previous_plan} people. {previous_arrivals} arrived.\\n'
            f'The next expedition can carry {current} people after {COOLDOWN_YEARS} in-game years of refitting.'
        ),
        'nym_failure_title': 'A Voyage Postponed',
        'nym_failure_desc': 'The expedition did not depart and no settlers were sent. You can organize another voyage when conditions allow.',
        'nym_pending_title': 'Word from Overseas',
        'nym_pending_desc': (
            'Reports from the ports are incomplete, so the government has put further departures on hold. '
            'To arrange this voyage again, load a save from before the expedition set out.'
        ),
        'nym_ack': 'Understood',
    }
    for lang, data in [('simp_chinese', zh), ('english', en)]:
        write(f'localization/{lang}/nanyang_l_{lang}.yml', f'l_{lang}:\n' + '\n'.join(f' {k}:0 "{v}"' for k, v in data.items()), bom=True)
    write('docs/design.json', json.dumps({'cultures': CULTURES, 'matrix': MATRIX,
          'regions': REGIONS, 'initial_target': INITIAL_TARGET, 'max_target': MAX_TARGET,
          'growth_percent': GROWTH_PERCENT, 'cooldown_years': COOLDOWN_YEARS,
          'targets': TARGETS, 'rounding': 'Hamilton, row-major tie break',
          'cell_plans': {str(t): apportion(t) for t in TARGETS}}, indent=2))

if __name__ == '__main__':
    main()

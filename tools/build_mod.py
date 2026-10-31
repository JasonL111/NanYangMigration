"""Generate the distributable native-script mod. Python is a development tool only."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'nanyang_migration'
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
TARGETS = [2000000, 2500000, 3125000, 3906250, 4882813, 5000000]
CELLS = [(r, c, w) for r, row in MATRIX.items() for c, w in zip(CULTURES, row) if w]

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
    for i in range(5):
        out += ('    if' if i == 0 else '    else_if') + f' = {{ limit = {{ nym_uses = {i} }} value = {nums[i]} }}\n'
    return out + '}\n'

def main():
    write('.metadata/metadata.json', json.dumps({
        'name': '下南洋 · Nanyang Migration', 'id': 'nanyang_migration',
        'version': '1.0.0', 'supported_game_version': '1.13.11',
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
    for region, states in REGIONS.items():
        triggers += f'nym_region_{region} = {{\n    exists = owner\n    OR = {{\n'
        triggers += ''.join(f'        state_region = s:STATE_{s}\n' for s in states)
        triggers += '    }\n}\n'
    write('common/scripted_triggers/nanyang_triggers.txt', triggers)
    values = '''# All counts are persons, not workforce. Explicit schedule avoids iterative rounding drift.
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
    values += table_value('nym_following_target', TARGETS[1:] + [5000000])
    for i, (r, c, _) in enumerate(CELLS):
        values += table_value(f'nym_plan_{r}_{c}', [apportion(t)[i] for t in TARGETS])
    values += '''
# Pop scope: cap against the click-time balance, live population and destination quota.
nym_take = {
    value = total_size
    min = var:nym_available
    min = scope:nym_country.var:nym_quota
    floor = yes
}
nym_state_share = {
    value = var:nym_cell_unassigned
    divide = var:nym_states_left
    floor = yes
}
nym_destination_delta = {
    value = scope:nym_destination.state_population
    subtract = var:nym_before
    max = 0
}
'''
    write('common/script_values/nanyang_values.txt', values)
    write('common/journal_entries/nanyang_journal.txt', '''
je_nanyang_migration = {
    group = je_group_foreign_affairs
    should_be_pinned_by_default_involved = yes
    transferable = no
    can_revolution_inherit = yes
    is_shown_when_inactive = { nym_eligible = yes }
    possible = { nym_eligible = yes }
    complete = { always = no }
    fail = { always = no }
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
            text = nym_cooldown_tt
            NOT = { has_global_variable = nym_cooldown }
        }
    }
    ai_chance = { value = 0 }
    effect = {
        # Timed persistent variable rather than unconditional button cooldown:
        # zero-move attempts must not consume cooldown; successor countries share it.
        if = {
            limit = { nym_eligible = yes NOT = { has_global_variable = nym_cooldown } }
            hidden_effect = { nym_execute = yes }
            custom_tooltip = nym_attempt_tt
        }
    }
}
''')
    effects = '''# Only executed on a player click; no periodic pop scans.
nym_execute = {
    save_scope_as = nym_country
    if = {
        limit = { NOT = { has_global_variable = nym_uses } }
        set_global_variable = { name = nym_uses value = 0 }
    }
    set_variable = { name = nym_requested value = nym_target }
    set_variable = { name = nym_actual value = 0 }
    # Snapshot the source objects and their pre-migration balance. Newly created
    # arrival objects are never added. Existing arrival objects cannot expand balances.
    every_scope_pop = {
        limit = { nym_culture = yes total_size >= 1 }
        set_variable = { name = nym_available value = total_size }
        set_variable = { name = nym_origin value = state }
        add_to_list = nym_sources
    }
'''
    for r in REGIONS:
        effects += f'''    set_variable = {{ name = nym_count_{r} value = 0 }}
    every_state = {{
        limit = {{ nym_region_{r} = yes }}
        add_to_list = nym_dest_{r}
        scope:nym_country = {{ change_variable = {{ name = nym_count_{r} add = 1 }} }}
    }}
'''
    for r, c, _ in CELLS:
        effects += f'    nym_run_cell = {{ REGION = {r} CULTURE = {c} AMOUNT = nym_plan_{r}_{c} }}\n'
    effects += '''    every_in_list = {
        list = nym_sources
        remove_variable = nym_available
        remove_variable = nym_origin
    }
    if = {
        limit = { var:nym_actual > 0 }
        set_global_variable = { name = nym_last value = var:nym_actual }
        set_global_variable = { name = nym_last_target value = var:nym_requested }
        change_global_variable = { name = nym_uses add = 1 }
        set_global_variable = { name = nym_cooldown value = yes years = 5 }
        trigger_event = { id = nanyang_migration.1 }
    }
    else = { trigger_event = { id = nanyang_migration.2 } }
}

# Country scope. Each nonzero matrix cell has its own unalterable budget.
# Missing regions are skipped; shortages never spill into another cell/culture.
nym_run_cell = {
    set_variable = { name = nym_cell_unassigned value = $AMOUNT$ }
    set_variable = { name = nym_states_left value = var:nym_count_$REGION$ }
    set_variable = { name = nym_cell_actual value = 0 }
    every_in_list = {
        list = nym_dest_$REGION$
        save_scope_as = nym_destination
        scope:nym_country = {
            set_variable = { name = nym_quota value = nym_state_share }
            change_variable = { name = nym_cell_unassigned subtract = var:nym_quota }
            change_variable = { name = nym_states_left subtract = 1 }
            every_in_list = {
                list = nym_sources
                limit = {
                    culture = cu:$CULTURE$
                    has_variable = nym_available
                    var:nym_available >= 1
                    total_size >= 1
                    state = var:nym_origin
                    state.owner = scope:nym_country
                    NOT = { state = scope:nym_destination }
                    scope:nym_country.var:nym_quota >= 1
                }
                nym_transfer = yes
            }
        }
    }
    # Per-cell actuals persist in the save for audit/debugging.
    set_global_variable = { name = nym_actual_$REGION$_$CULTURE$ value = var:nym_cell_actual }
}

# Pop scope. Debit before moving: native movement may delete or merge this pop.
# Record destination population delta, never the requested amount, as actual.
nym_transfer = {
    save_scope_value_as = { name = nym_amount value = nym_take }
    if = {
        limit = { scope:nym_amount >= 1 }
        change_variable = { name = nym_available subtract = scope:nym_amount }
        scope:nym_country = {
            set_variable = { name = nym_before value = scope:nym_destination.state_population }
        }
        move_partial_pop = { state = scope:nym_destination population = scope:nym_amount }
        scope:nym_country = {
            set_variable = { name = nym_delta value = nym_destination_delta }
            change_variable = { name = nym_actual add = var:nym_delta }
            change_variable = { name = nym_cell_actual add = var:nym_delta }
            change_variable = { name = nym_quota subtract = var:nym_delta }
        }
    }
}
'''
    write('common/scripted_effects/nanyang_effects.txt', effects)
    write('events/nanyang_events.txt', '''
namespace = nanyang_migration
nanyang_migration.1 = {
    type = country_event
    title = nym_success_title
    desc = nym_success_desc
    is_popup = yes
    option = { name = nym_ack }
}
nanyang_migration.2 = {
    type = country_event
    title = nym_failure_title
    desc = nym_failure_desc
    is_popup = yes
    option = { name = nym_ack }
}
''')
    dyn = lambda name: "[GetPlayer.MakeScope.ScriptValue('" + name + "')|0]"
    zh = {
        'je_nanyang_migration': '下南洋',
        'je_nanyang_migration_reason': '自闽粤沿海至南洋诸邦，华人远渡重洋、经商谋生，渐成海外聚落。国家可以组织大规模移民，使闽人、粤人、客家人与汉人迁往东南亚，在异域建立新的家园。\\n\\n累计成功：' + dyn('nym_uses') + ' 次；本次计划：' + dyn('nym_target') + ' 人。\\n上次计划：' + dyn('nym_last_target') + ' 人；上次实际完成：' + dyn('nym_last') + ' 人。\\n本次成功后的下一次目标：' + dyn('nym_following_target') + ' 人。冷却状态请查看按钮条件；成功后须等待5个游戏年。',
        'nym_organize_name': '组织下南洋',
        'nym_organize_desc': '本次计划迁移 ' + dyn('nym_target') + ' 人。来源为本国所有拥有的州，不设省份限制。\\n文化总比例：闽45%、粤30%、客家15%、汉10%。\\n目的地：马来亚及新加坡35%、荷属东印度25%、暹罗20%、印度支那12%、菲律宾5%、缅甸3%。按固定交叉矩阵执行；州内不设子地区权重，实际州等额分配并补整数余数。\\n成功后冷却5年，下一次增加25%，上限500万人。人口或有效目的地不足时仅完成可行部分；零迁移不扣次数与冷却。',
        'nym_cooldown_tt': '距离上一次成功组织下南洋已满5个游戏年（首次无需等待）',
        'nym_attempt_tt': '立即按固定文化与地理矩阵组织真实人口迁移；完成量见结果通知。',
        'nym_success_title': '南洋的新家园',
        'nym_success_desc': '本次目标：' + dyn('nym_last_target') + ' 人。\\n实际迁移：' + dyn('nym_last') + ' 人。\\n累计成功：' + dyn('nym_uses') + ' 次。下次目标：' + dyn('nym_target') + ' 人。\\n已进入5年冷却。人口不足或目的地不可用的份额不会用其他文化或地区补足。移民保留文化与宗教，抵达后按原生规则失业或转职。',
        'nym_failure_title': '航程未能启行',
        'nym_failure_desc': '没有实际转移任何人口。可能缺少四种文化的可迁移人口、有效目的州，或来源与目的相同。此次未增加成功次数，也未消耗冷却；上一次成功记录保持不变。',
        'nym_ack': '知悉',
    }
    en = {
        'je_nanyang_migration': 'Nanyang Migration',
        'je_nanyang_migration_reason': 'Chinese communities cross the seas to establish new homes in Southeast Asia. Organize immediate migration from all owned states.\\n\\nSuccessful expeditions: ' + dyn('nym_uses') + '. Current target: ' + dyn('nym_target') + ' persons.\\nLast target: ' + dyn('nym_last_target') + '; last actual: ' + dyn('nym_last') + '.\\nFollowing target after success: ' + dyn('nym_following_target') + '. Consult the button conditions for the five-year cooldown.',
        'nym_organize_name': 'Organize Nanyang Migration',
        'nym_organize_desc': 'Target: ' + dyn('nym_target') + ' persons from all owned states, without source province restrictions.\\nCultures: Min 45%, Yue 30%, Hakka 15%, Han 10%.\\nDestinations: Malaya/Singapore 35%, East Indies 25%, Siam 20%, Indochina 12%, Philippines 5%, Burma 3%, using the fixed cross-matrix. Equal shares across actual states with integer remainders.\\nFive-year cooldown on success; target grows by 25%, capped at 5 million. Shortages permit partial execution; zero movement consumes neither cooldown nor a successful use.',
        'nym_cooldown_tt': 'Five in-game years have elapsed since the last successful expedition (no wait for first use)',
        'nym_attempt_tt': 'Immediately transfer existing people using the fixed culture/geography matrix; see the result notification for actual movement.',
        'nym_success_title': 'New Homes in Nanyang',
        'nym_success_desc': 'Target: ' + dyn('nym_last_target') + ' persons.\\nActually moved: ' + dyn('nym_last') + '.\\nSuccessful expeditions: ' + dyn('nym_uses') + '. Next target: ' + dyn('nym_target') + '.\\nA five-year cooldown has begun. Unavailable shares are not reassigned. Migrants retain their culture and religion; native rules govern unemployment and occupational changes.',
        'nym_failure_title': 'The Expedition Could Not Depart',
        'nym_failure_desc': 'No people were actually transferred. Eligible source populations or valid destination states may be unavailable, or sources may coincide with destinations. No successful use or cooldown was consumed. The last successful record is unchanged.',
        'nym_ack': 'Understood',
    }
    for lang, data in [('simp_chinese', zh), ('english', en)]:
        write(f'localization/{lang}/nanyang_l_{lang}.yml', f'l_{lang}:\n' + '\n'.join(f' {k}:0 "{v}"' for k, v in data.items()), bom=True)
    write('docs/design.json', json.dumps({'cultures': CULTURES, 'matrix': MATRIX,
          'regions': REGIONS, 'targets': TARGETS, 'rounding': 'Hamilton, row-major tie break',
          'cell_plans': {str(t): apportion(t) for t in TARGETS}}, indent=2))

if __name__ == '__main__':
    main()

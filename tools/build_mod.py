"""Generate the distributable native-script mod. Python is a development tool only."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'nanyang_migration'
VERSION = '1.1.0-rc.2'
VERSION_LABEL = '1.1.0 RC2'
GAME_VERSION = '1.15.2'
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
    values += table_value('nym_following_target', TARGETS[1:] + [5000000])
    for i, (r, c, _) in enumerate(CELLS):
        values += table_value(f'nym_plan_{r}_{c}', [apportion(t)[i] for t in TARGETS])
    values += '''
# Pop scope: cap against the click-time balance, live population and destination quota.
nym_take = {
    value = total_size
    max = var:nym_available
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
        limit = { culture = scope:nym_current_culture }
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
    set_variable = { name = nym_last_request value = 0 }
    set_variable = { name = nym_source_delta value = 0 }
    set_variable = { name = nym_destination_delta value = 0 }

    # Only POPs present at click time can donate. The origin check also
    # protects against a split inheriting the variables of the old POP.
    every_scope_pop = {
        limit = { nym_culture = yes total_size >= 1 }
        set_variable = { name = nym_available value = total_size days = 1 }
        state = { save_scope_as = nym_snapshot_state }
        set_variable = { name = nym_origin value = scope:nym_snapshot_state days = 1 }
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
        cu:{culture} = {{ save_scope_as = nym_current_culture }}
        set_variable = {{ name = nym_cell_unassigned value = nym_plan_{region}_{culture} }}
        set_variable = {{ name = nym_states_left value = var:nym_count_{region} }}
        set_variable = {{ name = nym_cell_actual value = 0 }}
        nym_visit_{region} = yes
        set_global_variable = {{ name = {record} value = var:nym_cell_actual }}
    }}
'''
    effects += '''    every_scope_pop = {
        limit = { has_variable = nym_available }
        remove_variable = nym_available
        remove_variable = nym_origin
    }
    if = {
        limit = { has_variable = nym_transfer_halted }
        # Retain the save-wide operation lock, even if the native effect was a no-op.
        remove_variable = nym_transfer_halted
        trigger_event = { id = nanyang_migration.3 }
    }
    else_if = {
        limit = { var:nym_actual > 0 }
        set_global_variable = { name = nym_last value = var:nym_actual }
        set_global_variable = { name = nym_last_target value = var:nym_requested }
        change_global_variable = { name = nym_uses add = 1 }
        set_global_variable = { name = nym_cooldown value = yes years = 5 }
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
                every_scope_pop = {
                    limit = {
                        culture = scope:nym_current_culture
                        has_variable = nym_available
                    }
                    # Recheck mutable guards in the body after each native move.
                    if = {
                        limit = {
                            scope:nym_country = {
                                NOT = { has_variable = nym_transfer_halted }
                                var:nym_quota >= 1
                            }
                            var:nym_available >= 1
                            total_size >= 1
                            state = var:nym_origin
                            owner = scope:nym_country
                            NOT = { state = scope:nym_destination }
                        }
                        scope:nym_country = { change_variable = { name = nym_source_matches add = 1 } }
                        nym_transfer = yes
                    }
                }
            }
        }
    }
}

# POP scope on entry. After the native effect use only the saved country and states.
nym_transfer = {
    save_scope_value_as = { name = nym_amount value = nym_take }
    if = {
        limit = { scope:nym_amount >= 1 }
        state = { save_scope_as = nym_origin_state }
        change_variable = { name = nym_available subtract = scope:nym_amount }
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
nanyang_migration.3 = {
    type = country_event
    title = nym_pending_title
    desc = nym_pending_desc
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
        'nym_failure_desc': '本次记录的迁入量为零，因此未增加成功次数或消耗冷却。这不等于全国人口不足：请检查可迁移文化、有效目的州以及脚本错误日志。若人口实际变化而记录为零，属于脚本或统计错误；上一次成功记录保持不变。',
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
        'nym_failure_desc': 'Recorded arrivals are zero. No successful use or cooldown was consumed. This does not establish a national population shortage: check eligible cultures, destinations and script error logs. If populations changed despite a zero record, this is a script or accounting error. The last successful record is unchanged.',
        'nym_ack': 'Understood',
    }
    for lang, data in [('simp_chinese', zh), ('english', en)]:
        val = lambda name: "[GetPlayer.MakeScope.Var('" + name + "').GetValue|0]"
        if lang == 'simp_chinese':
            diagnostic = (f'\\n\\n{VERSION_LABEL} 诊断：来源POP数 ' + val('nym_source_count') + '；来源总人口 ' + val('nym_source_people')
                + '。\\n目的州数（马来亚/东印度/暹罗/印度支那/菲律宾/缅甸）：'
                + '/'.join(val('nym_count_'+r) for r in REGIONS)
                + '。\\n启动配额 ' + val('nym_cells_started') + '；正额度州份数 ' + val('nym_positive_shares')
                + '；通过筛选的来源与目的配对 ' + val('nym_source_matches')
                + '。\\n转移调用次数 ' + val('nym_transfer_calls') + '；请求人口合计 ' + val('nym_transfer_requested')
                + '；记录迁入合计 ' + val('nym_actual') + '。\\n若进入待确认，请保留截图与本次 error.log。')
            data['nym_failure_title'] = '下南洋：本次未发出转移请求'
            data['nym_failure_desc'] = '本次没有调用原生人口移动效果。诊断依次显示来源、目的州、额度、配对和调用次数。'
        else:
            diagnostic = (f'\\n\\n{VERSION_LABEL} diagnostics: source POPs ' + val('nym_source_count') + '; source persons ' + val('nym_source_people')
                + '.\\nDestination states (Malaya/East Indies/Siam/Indochina/Philippines/Burma): '
                + '/'.join(val('nym_count_'+r) for r in REGIONS)
                + '.\\nAllocation cells started ' + val('nym_cells_started') + '; positive state shares ' + val('nym_positive_shares')
                + '; eligible source-to-destination pairs ' + val('nym_source_matches')
                + '.\\nMove calls ' + val('nym_transfer_calls') + '; requested persons ' + val('nym_transfer_requested')
                + '; recorded arrivals ' + val('nym_actual')
                + '.\\nIf verification is blocked, retain this report and error.log.')
            data['nym_failure_title'] = 'Nanyang: No Transfer Requested'
            data['nym_failure_desc'] = 'No native move was called. The diagnostics show sources, destinations, allocation, eligible pairs and move calls.'
        if lang == 'simp_chinese':
            data['nym_pending_tt'] = '上次转移尚未确认。请查看结果和日志，或载入操作前的存档。'
            data['nym_pending_title'] = '下南洋：迁移待确认'
            data['nym_pending_desc'] = '本次移动后的来源与目的 POP 读数未能确认同一笔转移。已停止后续移动并锁定重试。'
            diagnostic += ('\\n末笔请求 ' + val('nym_last_request') + '；来源减少 ' + val('nym_source_delta')
                           + '；目的增加 ' + val('nym_destination_delta') + '。')
        else:
            data['nym_pending_tt'] = 'The previous transfer is unconfirmed. Check the report and logs or load a save from before the attempt.'
            data['nym_pending_title'] = 'Nanyang: Transfer Unconfirmed'
            data['nym_pending_desc'] = 'The source and destination POP readings did not confirm the same transfer. Further moves and retries are locked.'
            diagnostic += ('\\nLast request ' + val('nym_last_request') + '; source decrease ' + val('nym_source_delta')
                           + '; destination increase ' + val('nym_destination_delta') + '.')
        data['nym_pending_desc'] += diagnostic
        data['nym_failure_desc'] += diagnostic
        data['nym_success_desc'] += diagnostic
        write(f'localization/{lang}/nanyang_l_{lang}.yml', f'l_{lang}:\n' + '\n'.join(f' {k}:0 "{v}"' for k, v in data.items()), bom=True)
    write('docs/design.json', json.dumps({'cultures': CULTURES, 'matrix': MATRIX,
          'regions': REGIONS, 'targets': TARGETS, 'rounding': 'Hamilton, row-major tie break',
          'cell_plans': {str(t): apportion(t) for t in TARGETS}}, indent=2))

if __name__ == '__main__':
    main()

"""Generate a separate, once-per-save, small-move native diagnostic."""
import json

from build_mod import ROOT, GAME_VERSION

PROBE = ROOT / 'diagnostics/nanyang_native_probe'
PROBE_VERSION = '1.1.1'
MODES = {
    'literal': 'population = 100',
    'dynamic': 'population = scope:nyp_amount',
    'ratio': 'population_ratio = 0.1',
    'whole': '',
}
MEASURES = {'live': 'total_size', 'work': 'workforce', 'deps': 'dependents', 'objects': '1'}

def write(path, contents, bom=False):
    target = PROBE / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(contents.strip() + '\n', encoding='utf-8-sig' if bom else 'utf-8')

def main():
    write('.metadata/metadata.json', json.dumps({
        'name': 'Nanyang Native POP Probe', 'id': 'nanyang_native_probe', 'version': PROBE_VERSION,
        'supported_game_version': GAME_VERSION, 'relationships': [],
        'short_description': 'Single small POP experiment for a disposable 1836 save.',
        'tags': ['Gameplay'], 'game_custom_data': {'multiplayer_synchronized': True},
    }, indent=2))
    write('common/journal_entries/nanyang_probe.txt', '''
je_nyp_native = {
    group = je_group_foreign_affairs
    context = country
    is_shown_when_inactive = { is_player = yes country_definition = cd:CHI }
    possible = { is_player = yes country_definition = cd:CHI }
''' + ''.join(f'    scripted_button = nyp_button_{mode}\n' for mode in MODES) + '}')
    buttons = ''
    methods = ''
    for mode, arg in MODES.items():
        min_size, max_size = (1, 1000) if mode == 'whole' else (1000, 10000)
        buttons += f'''
nyp_button_{mode} = {{
    name = nyp_label_{mode}
    desc = nyp_button_desc
    visible = {{ is_player = yes country_definition = cd:CHI }}
    possible = {{ NOT = {{ has_global_variable = nyp_started }} }}
    ai_chance = {{ base = 0 }}
    effect = {{
        if = {{
            limit = {{
                is_player = yes country_definition = cd:CHI
                NOT = {{ has_global_variable = nyp_started }}
            }}
            hidden_effect = {{ nyp_test_{mode} = yes }}
            custom_tooltip = nyp_button_desc
        }}
    }}
}}
'''
        methods += f'''
nyp_test_{mode} = {{
    save_scope_as = nyp_actor
    s:STATE_MALAYA ?= {{
        random_scope_state = {{
            limit = {{ exists = owner NOT = {{ owner = scope:nyp_actor }} }}
            save_scope_as = nyp_destination
        }}
    }}
    if = {{
        limit = {{ exists = scope:nyp_destination }}
        random_scope_pop = {{
            limit = {{ culture = cu:min total_size >= {min_size} total_size <= {max_size} workforce >= 1 dependents >= 1 }}
            save_scope_as = nyp_pop
            state = {{ save_scope_as = nyp_source }}
        }}
    }}
    if = {{
        limit = {{ exists = scope:nyp_pop }}
        set_global_variable = {{ name = nyp_started value = yes }}
        nyp_sample_before = yes
        save_scope_value_as = {{ name = nyp_amount value = 100 }}
        scope:nyp_pop = {{ move_partial_pop = {{ state = scope:nyp_destination {arg} }} }}
        nyp_sample_after = yes
        trigger_event = {{ id = nanyang_native_probe.1 }}
        trigger_event = {{ id = nanyang_native_probe.2 days = 1 }}
    }}
    else = {{ trigger_event = {{ id = nanyang_native_probe.3 }} }}
}}
'''
    values = ''.join(f'''
nyp_{key} = {{
    value = 0
    every_scope_pop = {{ limit = {{ culture = cu:min }} add = {value} }}
}}
''' for key, value in MEASURES.items())
    write('common/script_values/nanyang_probe.txt', values)
    for moment in ('before', 'after', 'day'):
        methods += f'\nnyp_sample_{moment} = {{\n'
        for endpoint in ('source', 'destination'):
            for label, value in {'cache': 'state_population', **{k: 'nyp_'+k for k in MEASURES}}.items():
                name = f'nyp_{moment}_{endpoint}_{label}'
                methods += f'''    set_variable = {{ name = {name} value = -1 }}
    if = {{
        limit = {{ exists = scope:nyp_{endpoint} }}
        set_variable = {{ name = {name} value = scope:nyp_{endpoint}.{value} }}
    }}
'''
        for label, value in {'live': 'total_size', 'work': 'workforce', 'deps': 'dependents'}.items():
            name = f'nyp_{moment}_object_{label}'
            methods += f'''    set_variable = {{ name = {name} value = -1 }}
    if = {{
        limit = {{ exists = scope:nyp_pop }}
        set_variable = {{ name = {name} value = scope:nyp_pop.{value} }}
    }}
'''
        methods += f'''    set_variable = {{ name = nyp_{moment}_object_at_destination value = 0 }}
    if = {{
        limit = {{ exists = scope:nyp_pop scope:nyp_pop.state = scope:nyp_destination }}
        set_variable = {{ name = nyp_{moment}_object_at_destination value = 1 }}
    }}
}}
'''
    write('common/scripted_buttons/nanyang_probe.txt', buttons)
    write('common/scripted_effects/nanyang_probe.txt', methods)
    write('events/nanyang_probe.txt', '''
namespace = nanyang_native_probe
nanyang_native_probe.1 = {
    type = country_event
    title = nyp_title_now
    desc = nyp_now
    is_popup = yes
    option = { name = nyp_ack }
}
nanyang_native_probe.2 = {
    type = country_event
    immediate = { nyp_sample_day = yes }
    title = nyp_title_day
    desc = nyp_day
    is_popup = yes
    option = { name = nyp_ack }
}
nanyang_native_probe.3 = {
    type = country_event
    title = nyp_title_none
    desc = nyp_none
    is_popup = yes
    option = { name = nyp_ack }
}
''')
    for lang in ('english', 'simp_chinese'):
        zh = lang == 'simp_chinese'
        titles = ['常数 100', '动态 100', '比例 10%', '整个 POP（至多 1000）'] if zh else [
            'Literal 100', 'Dynamic 100', 'Ratio 10%', 'Whole POP (up to 1000)']
        data = {f'nyp_label_{mode}': title for mode, title in zip(MODES, titles)}
        data.update({
            'je_nyp_native': '下南洋原生迁移诊断' if zh else 'Nanyang Native Transfer Probe',
            'je_nyp_native_reason': '独立测试档中执行一项，然后从原备份另测。' if zh else 'Run one experiment in a test save. Reload the baseline for the next.',
            'nyp_button_desc': '执行一次小额跨境实验。请先存档。' if zh else 'Run one small cross-border experiment. Save first.',
            'nyp_title_now': '原生诊断：即时读数' if zh else 'Native probe: same effect',
            'nyp_title_day': '原生诊断：隔日读数' if zh else 'Native probe: next day',
            'nyp_title_none': '未选中测试对象' if zh else 'No probe target selected',
            'nyp_none': '未找到外国持有的马来亚实际州或符合大小范围的闽文化 POP。未调用迁移。' if zh else 'No foreign-owned Malaya state or eligible Min POP in the size range. No move called.',
            'nyp_ack': '确定' if zh else 'OK',
        })
        def number(moment, endpoint, label):
            return f"[ROOT.GetCountry.MakeScope.Var('nyp_{moment}_{endpoint}_{label}').GetValue|0]"
        def readout(moment):
            label = {'before': '移动前 / Before', 'after': '同脚本 / Same effect', 'day': '隔日 / Next day'}[moment]
            lines = [label]
            for endpoint, title in [('source', '来源 / Source'), ('destination', '目的 / Destination'),
                                    ('object', '原 POP / Original POP')]:
                measures = ('cache', *MEASURES) if endpoint != 'object' else ('live', 'work', 'deps', 'at_destination')
                lines.append(title + '  ' + ' / '.join(number(moment, endpoint, k) for k in measures))
            return '\\n'.join(lines)
        legend = ('州读数依次为全州统计 / 闽人口 / 闽劳力 / 闽家属 / 闽 POP 数。原 POP 依次为大小 / 劳力 / 家属 / 是否在目的州。-1 表示引用不可读。'
                  if zh else 'State readings: cached total / Min live total / workforce / dependents / objects. Original POP: total / workforce / dependents / at destination. -1 means scope unavailable.')
        state_names = "[SCOPE.sState('nyp_source').GetName] → [SCOPE.sState('nyp_destination').GetName]"
        data['nyp_now'] = state_names + '\\n' + legend + '\\n\\n' + readout('before') + '\\n\\n' + readout('after')
        data['nyp_day'] = state_names + '\\n' + legend + '\\n\\n' + readout('day')
        write(f'localization/{lang}/nanyang_probe_l_{lang}.yml', f'l_{lang}:\n' +
              '\n'.join(f' {k}:0 "{v}"' for k, v in data.items()), bom=True)

if __name__ == '__main__':
    main()

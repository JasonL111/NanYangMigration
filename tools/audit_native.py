"""Recheck pinned native documentation and optionally audit a local 1.15.2 install.

Reads installed game data. Prints identifiers and file digests, never source files.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re

from build_mod import CULTURES, REGIONS, GAME_VERSION

DOC_SYMBOLS = {
    'effects.log': ('move_partial_pop', 'every_scope_pop', 'every_scope_state', 'random_scope_pop',
                    'random_scope_state', 'add_to_list', 'every_in_list', 'save_scope_as',
                    'save_scope_value_as', 'set_variable', 'change_variable', 'remove_variable',
                    'set_global_variable', 'change_global_variable', 'remove_global_variable',
                    'trigger_event', 'hidden_effect', 'custom_tooltip'),
    'triggers.log': ('exists', 'is_player', 'has_variable', 'has_global_variable',
                     'total_size', 'state_population', 'workforce', 'dependents'),
    'event_targets.log': ('country_definition', 'civil_war_origin_country', 'culture', 'cu', 'cd', 's',
                          'state_region', 'region_state', 'state', 'owner', 'var', 'scope', 'global_var'),
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check_docs(repo):
    output = {}
    for name, symbols in DOC_SYMBOLS.items():
        path = repo / GAME_VERSION / 'docs' / name
        data = path.read_text(encoding='utf-8-sig', errors='replace')
        missing = [x for x in symbols if not re.search(r'^#{2,3} ' + re.escape(x) + r'\s*$', data, re.M)]
        if missing:
            raise ValueError(f'{path}: undocumented symbols: {missing}')
        output[str(path.relative_to(repo))] = sha(path)
    for name, path in {
        'journal_entries': '1.15.0/types/journal_entries.md',
        'scripted_buttons': '1.15.0/types/scripted_buttons.md',
        'script_values': 'documentation/types/script_values.md',
        'event_scopes': GAME_VERSION+'/docs/event_scopes.log',
        'localization_data_types': GAME_VERSION+'/docs/data_types_script.txt',
    }.items():
        output[path] = sha(repo/path)
    return output

def check_game(game):
    expected = {
        'common/cultures': set(CULTURES),
        'common/country_definitions': {'CHI'},
        'common/journal_entry_groups': {'je_group_foreign_affairs'},
        'map_data/state_regions': {'STATE_'+s for states in REGIONS.values() for s in states},
    }
    evidence = {}
    for rel, pending in expected.items():
        matched = {}
        for path in sorted((game/rel).glob('*.txt')):
            data = path.read_text(encoding='utf-8-sig', errors='replace')
            found = pending & set(re.findall(r'^\s*(\w+)\s*=\s*\{', data, re.M))
            if found:
                matched[path.name] = {'ids': sorted(found), 'sha256': sha(path)}
                pending -= found
        if pending:
            raise ValueError(f'{rel}: unresolved {sorted(pending)}')
        evidence[rel] = matched
    return evidence

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--digest', type=Path)
    parser.add_argument('--game-data', type=Path, help='game directory under an installed copy')
    parser.add_argument('--game-version', help='installed version shown in the game menu')
    args = parser.parse_args()
    if not args.digest and not args.game_data:
        parser.error('supply --digest and/or --game-data')
    if args.digest:
        print(json.dumps({'native_docs': check_docs(args.digest)}, indent=2))
    if args.game_data:
        if args.game_version != GAME_VERSION:
            parser.error(f'confirm the installed version with --game-version {GAME_VERSION}')
        print(json.dumps({'user_reported_game_version': args.game_version,
                          'identifiers': check_game(args.game_data)}, indent=2))

if __name__ == '__main__':
    main()

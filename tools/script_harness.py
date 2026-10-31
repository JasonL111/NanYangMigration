"""Small, strict interpreter for THIS mod's script subset, NOT a game emulator.

Executes the emitted scripts against synthetic states/pops to test accounting and
control flow. Native effects, object merging, timers and data caches still require
Victoria 3. Unknown constructs fail rather than silently passing.
"""
from pathlib import Path
from dataclasses import dataclass, field
import re

TOKEN = re.compile(r'"(?:\\.|[^"\\])*"|\?=|>=|<=|!=|[{}=<>]|[^\s{}=<>!]+')

def parse(text):
    text = re.sub(r'#.*', '', text.lstrip('\ufeff'))
    tokens = TOKEN.findall(text)
    index = 0
    def block(nested=False):
        nonlocal index
        result = []
        while index < len(tokens):
            if tokens[index] == '}':
                if not nested:
                    raise ValueError('Unexpected closing brace')
                index += 1
                return result
            key = tokens[index]
            index += 1
            if index >= len(tokens) or tokens[index] not in ('=', '>', '<', '>=', '<=', '!=', '?='):
                raise ValueError(f'Expected operator after {key}')
            op = tokens[index]
            index += 1
            if tokens[index] == '{':
                index += 1
                value = block(True)
            else:
                value = tokens[index].strip('"')
                index += 1
            result.append((key, op, value))
        if nested:
            raise ValueError('Unclosed block')
        return result
    return block()

def fields(block):
    return {k: v for k, _, v in block}

@dataclass(eq=False)
class Country:
    definition: str = 'cd:CHI'
    player: bool = True
    vars: dict = field(default_factory=dict)

@dataclass(eq=False)
class State:
    region: str
    owner: Country
    vars: dict = field(default_factory=dict)

@dataclass(eq=False)
class Pop:
    state: State
    culture: str
    size: int
    religion: str = 'confucian'
    vars: dict = field(default_factory=dict)

class Harness:
    def __init__(self, mod):
        self.defs = {}
        for f in (Path(mod)/'common').rglob('*.txt'):
            for key, _, value in parse(f.read_text(encoding='utf-8-sig')):
                if key in self.defs:
                    raise ValueError('Duplicate definition: '+key)
                self.defs[key] = value
        self.country = Country()
        self.states = []
        self.pops = []
        self.globals = {}
        self.saved = {}
        self.lists = {}
        self.events = []
        self.durations = {}
        self.moved = 0
        self.transfers = []

    def population(self, state):
        return sum(p.size for p in self.pops if p.state is state)

    def resolve(self, name, obj):
        if not isinstance(name, str):
            return self.formula(name, obj)
        try:
            return float(name) if '.' in name else int(name)
        except ValueError:
            pass
        if name in ('yes', 'no'):
            return name == 'yes'
        if name in ('this', 'THIS'):
            return obj
        if name in ('root', 'ROOT'):
            return self.country
        if name.startswith(('cu:', 'cd:', 's:')):
            return name
        if '.' in name:
            a, rest = name.split('.', 1)
            return self.resolve(rest, self.resolve(a, obj))
        if name.startswith('scope:'):
            return self.saved.get(name[6:])
        if name.startswith('var:'):
            return obj.vars.get(name[4:]) if obj else None
        if name.startswith('global_var:'):
            return self.globals.get(name[11:])
        if name in self.defs:
            return self.formula(self.defs[name], obj)
        if obj is None:
            return None
        native = {
            'total_size': lambda: obj.size,
            'state_population': lambda: self.population(obj),
            'state': lambda: obj.state,
            'owner': lambda: obj.owner,
            'culture': lambda: 'cu:'+obj.culture,
            'state_region': lambda: 's:STATE_'+obj.region,
            'country_definition': lambda: obj.definition,
            'is_player': lambda: obj.player,
            'civil_war_origin_country': lambda: None,
        }
        if name not in native:
            raise ValueError('Unknown reference '+name)
        return native[name]()

    def condition(self, block, obj):
        result = []
        for key, op, value in block:
            if key == 'OR':
                result.append(any(self.condition([entry], obj) for entry in value))
            elif key == 'AND':
                result.append(self.condition(value, obj))
            elif key == 'NOT':
                result.append(not self.condition(value, obj))
            elif key == 'custom_tooltip':
                result.append(self.condition([e for e in value if e[0] != 'text'], obj))
            elif key == 'always':
                result.append(value == 'yes')
            elif key == 'exists':
                result.append(self.resolve(value, obj) is not None)
            elif key == 'has_variable':
                result.append(value in obj.vars)
            elif key == 'has_global_variable':
                result.append(value in self.globals)
            elif key in self.defs and key.startswith(('nym_region_', 'nym_culture', 'nym_eligible')):
                result.append(self.condition(self.defs[key], obj) == (value == 'yes'))
            elif isinstance(value, list):
                result.append(self.condition(value, self.resolve(key, obj)))
            else:
                a, b = self.resolve(key, obj), self.resolve(value, obj)
                if op in ('=', '?='):
                    result.append(a == b and (op != '?=' or a is not None))
                elif op == '!=':
                    result.append(a != b)
                else:
                    result.append({'<': lambda:a < b, '>': lambda:a > b,
                                   '<=':lambda:a <= b, '>=':lambda:a >= b}[op]())
        return all(result)

    def formula(self, block, obj):
        import math
        out, branch = 0, False
        for key, _, value in block:
            if key in ('if', 'else_if'):
                f = fields(value)
                if (key == 'if' or not branch) and self.condition(f['limit'], obj):
                    out = self.formula([('value', '=', str(out))]+[e for e in value if e[0] != 'limit'], obj)
                    branch = True
                elif key == 'if':
                    branch = False
            elif key == 'floor':
                out = math.floor(out)
            elif key == 'value':
                out = self.resolve(value, obj)
            else:
                val = self.resolve(value, obj)
                if key == 'min': out = min(out, val)
                elif key == 'max': out = max(out, val)
                elif key == 'add': out += val
                elif key == 'subtract': out -= val
                elif key == 'divide': out /= val
                else: raise ValueError('Unknown arithmetic '+key)
        return out

    def run(self, block, obj=None):
        obj = self.country if obj is None else obj
        branch = False
        for key, _, value in block:
            f = fields(value) if isinstance(value, list) else {}
            if key in ('if', 'else_if', 'else'):
                take = (key == 'if' or not branch) and (key == 'else' or self.condition(f['limit'], obj))
                if key == 'if': branch = False
                if take:
                    self.run([e for e in value if e[0] != 'limit'], obj)
                    branch = True
            elif key in ('hidden_effect',):
                self.run(value, obj)
            elif key in ('custom_tooltip',):
                pass
            elif key.startswith('scope:'):
                self.run(value, self.resolve(key, obj))
            elif key in ('set_variable', 'set_global_variable'):
                store = self.globals if key == 'set_global_variable' else obj.vars
                store[f['name']] = self.resolve(f.get('value', 'yes'), obj)
                if 'years' in f: self.durations[f['name']] = ('years', int(f['years']))
            elif key in ('change_variable', 'change_global_variable'):
                store = self.globals if key == 'change_global_variable' else obj.vars
                operation = next(x for x in f if x != 'name')
                val = self.resolve(f[operation], obj)
                store[f['name']] += val if operation == 'add' else -val
            elif key == 'remove_variable':
                obj.vars.pop(value, None)
            elif key == 'save_scope_as':
                self.saved[value] = obj
            elif key == 'save_scope_value_as':
                self.saved[f['name']] = self.resolve(f['value'], obj)
            elif key == 'add_to_list':
                self.lists.setdefault(value, []).append(obj)
            elif key in ('every_scope_pop', 'every_state', 'every_in_list'):
                if key == 'every_scope_pop':
                    items = [p for p in self.pops if p.state.owner is obj and p.size > 0]
                elif key == 'every_state':
                    items = list(self.states)
                else:
                    items = list(self.lists.get(f['list'], []))
                for item in items:
                    if isinstance(item, Pop) and item.size == 0: continue
                    if self.condition(f.get('limit', []), item):
                        self.run([e for e in value if e[0] not in ('limit', 'list')], item)
            elif key == 'move_partial_pop':
                destination = self.resolve(f['state'], obj)
                amount = self.resolve(f['population'], obj)
                assert 0 < amount <= obj.size and destination is not obj.state
                old = obj.state
                obj.size -= amount
                # Simulate native merging; original object may have been in the source snapshot.
                match = next((p for p in self.pops if p.state is destination and p.culture == obj.culture and p.religion == obj.religion and p.size > 0), None)
                if match: match.size += amount
                else: self.pops.append(Pop(destination, obj.culture, amount, obj.religion))
                self.moved += amount
                self.transfers.append((old, destination, obj.culture, amount))
            elif key == 'trigger_event':
                self.events.append(f['id'] if f else value)
            elif key in self.defs:
                source = self.defs[key]
                if f:
                    # Expand parameterized scripted effects exactly where invoked.
                    source = repr(source)
                    for param, replacement in f.items():
                        source = source.replace('$'+param+'$', replacement)
                    import ast
                    source = ast.literal_eval(source)
                self.run(source, obj)
            else:
                raise ValueError('Unknown effect '+key)

    def click(self):
        self.lists, self.saved = {}, {}
        button = fields(self.defs['nym_organize'])
        if self.condition(button['possible'], self.country):
            self.run(button['effect'])

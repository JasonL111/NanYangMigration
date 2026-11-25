"""Small, strict interpreter for THIS mod's script subset, NOT a game emulator.

Executes the emitted scripts against synthetic states/pops to test accounting and
control flow. Native effects, object merging, timers and data caches still require
Victoria 3. Unknown constructs fail rather than silently passing.
"""
from pathlib import Path
from dataclasses import dataclass, field
from fractions import Fraction
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
    origin: "Country | None" = None

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
    def __init__(self, mod, *, move=None, ignore_pop_writes=False, ignore_state_writes=False):
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
        self.move = move
        # Fault injection only. It does not assert these faults occur in Victoria 3.
        self.ignore_pop_writes = ignore_pop_writes
        self.ignore_state_writes = ignore_state_writes
        self.cached_population = {}
        self.delayed_moves = []

    def population(self, state):
        return sum(p.size for p in self.pops if p.state is state)

    def resolve(self, name, obj):
        if isinstance(name, list):
            return self.formula(name, obj)
        if not isinstance(name, str):
            return name
        try:
            return Fraction(name) if '.' in name else int(name)
        except ValueError:
            pass
        if name in ('yes', 'no'):
            return name == 'yes'
        if name in ('this', 'THIS'):
            return obj
        if name in ('root', 'ROOT'):
            return self.country
        if '.' in name:
            a, rest = name.split('.', 1)
            return self.resolve(rest, self.resolve(a, obj))
        if name.startswith(('cu:', 'cd:')):
            return name
        if name.startswith('s:STATE_'):
            return name if any(s.region == name[8:] for s in self.states) else None
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
            'state_population': lambda: self.cached_population.get(obj, self.population(obj)),
            'state': lambda: obj.state,
            'owner': lambda: obj.state.owner if isinstance(obj, Pop) else obj.owner,
            'culture': lambda: 'cu:'+obj.culture,
            'state_region': lambda: 's:STATE_'+obj.region,
            'country_definition': lambda: obj.definition,
            'is_player': lambda: obj.player,
            'civil_war_origin_country': lambda: obj.origin,
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
            elif key in self.defs and key.startswith(('nym_culture', 'nym_eligible')):
                result.append(self.condition(self.defs[key], obj) == (value == 'yes'))
            elif isinstance(value, list):
                target = self.resolve(key, obj)
                result.append(target is not None and self.condition(value, target))
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
                    out = self.formula([('value', '=', out)]+[e for e in value if e[0] != 'limit'], obj)
                    branch = True
                elif key == 'if':
                    branch = False
            elif key == 'every_scope_pop':
                f = fields(value)
                for pop in self.scope_pops(obj):
                    if self.condition(f.get('limit', []), pop):
                        out += self.formula([e for e in value if e[0] != 'limit'], pop)
            elif key == 'floor':
                out = math.floor(out)
            elif key == 'value':
                out = self.resolve(value, obj)
            else:
                val = self.resolve(value, obj)
                # Jomini min/max specify lower/upper BOUNDS, not Python functions.
                if key == 'min': out = max(out, val)
                elif key == 'max': out = min(out, val)
                elif key == 'add': out += val
                elif key == 'subtract': out -= val
                elif key == 'divide': out = Fraction(out) / val
                else: raise ValueError('Unknown arithmetic '+key)
        return out

    def run(self, block, obj=None):
        obj = self.country if obj is None else obj
        branch = False
        for key, operator, value in block:
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
            elif key == 'state' or key.startswith(('scope:', 's:', 'cu:')):
                target = self.resolve(key, obj)
                if target is not None:
                    self.run(value, target)
                elif operator != '?=':
                    raise ValueError('Invalid required scope: ' + key)
            elif key in ('set_variable', 'set_global_variable'):
                if key == 'set_variable' and (
                    (isinstance(obj, Pop) and self.ignore_pop_writes)
                    or (isinstance(obj, State) and self.ignore_state_writes)
                ):
                    continue
                store = self.globals if key == 'set_global_variable' else obj.vars
                if not f:
                    store[value] = True
                    continue
                store[f['name']] = self.resolve(f.get('value', 'yes'), obj)
                if 'years' in f: self.durations[f['name']] = ('years', int(f['years']))
            elif key in ('change_variable', 'change_global_variable'):
                store = self.globals if key == 'change_global_variable' else obj.vars
                operation = next(x for x in f if x != 'name')
                val = self.resolve(f[operation], obj)
                store[f['name']] += val if operation == 'add' else -val
            elif key == 'remove_variable':
                obj.vars.pop(value, None)
            elif key == 'remove_global_variable':
                self.globals.pop(value, None)
            elif key == 'save_scope_as':
                self.saved[value] = obj
            elif key == 'save_scope_value_as':
                self.saved[f['name']] = self.resolve(f['value'], obj)
            elif key == 'add_to_list':
                self.lists.setdefault(value, []).append(obj)
            elif key in ('every_scope_pop', 'every_scope_state', 'every_state', 'every_in_list'):
                if key == 'every_scope_pop':
                    items = self.scope_pops(obj)
                elif key == 'every_scope_state':
                    items = [s for s in self.states if obj == 's:STATE_'+s.region or s.owner is obj]
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
                if self.move is None:
                    raise NotImplementedError('A native migration scenario must be supplied')
                self.move(self, obj, destination, amount)
            elif key == 'trigger_event':
                self.events.append(f['id'] if f else value)
            elif key in self.defs:
                source = self.defs[key]
                if f:
                    def expand(token):
                        if isinstance(token, list):
                            return [(expand(k), op, expand(v)) for k, op, v in token]
                        if '$' not in token:
                            return token
                        if not (token.startswith('$') and token.endswith('$') and token.count('$') == 2):
                            raise ValueError('Only whole-token scripted-effect parameters are modeled')
                        return f[token[1:-1]]
                    source = expand(source)
                self.run(source, obj)
            else:
                raise ValueError('Unknown effect '+key)

    def scope_pops(self, obj):
        if isinstance(obj, State):
            return [p for p in self.pops if p.state is obj and p.size > 0]
        if isinstance(obj, Country):
            return [p for p in self.pops if p.state.owner is obj and p.size > 0]
        raise ValueError('Unsupported scope for POP iteration')

    def apply_move(self, pop, destination, amount):
        """Explicit synthetic model. A fully consumed source leaves iteration."""
        old = pop.state
        pop.size -= amount
        match = next((other for other in self.scope_pops(destination)
                      if other.culture == pop.culture and other.religion == pop.religion), None)
        if match:
            match.size += amount
        else:
            self.pops.append(Pop(destination, pop.culture, amount, pop.religion))
        self.moved += amount
        self.transfers.append((old, destination, pop.culture, amount))

    def tick(self):
        for args in self.delayed_moves:
            self.apply_move(*args)
        self.delayed_moves.clear()
        self.cached_population.clear()

    def click(self):
        self.lists, self.saved = {}, {}
        button = fields(self.defs['nym_organize'])
        if self.condition(button['possible'], self.country):
            self.run(button['effect'])

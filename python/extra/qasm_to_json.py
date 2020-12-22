##
## Convert QASM to JSON, and vice versa
##

import sys
import re
import json
from typing import List, Dict, Match, Optional

## quantum gate: translate qasm to json
def to_json_quantum_gate(m: Match[str], c: List[Dict]) -> Optional[List[Dict]]:
  q = m.group('qubits')
  if q is None or \
     not (qubits := [
       {'name': q, 'idx': int(n)} for q, n in re.findall(r'(\w+)\[(\d)\]', q)]):
    print('None qubits', file=sys.stderr)
    return None
  c.append({
    'name': m.group('name'),
    'param': m.group('param'),
    'control': qubits[:1] if len(qubits) > 1 else [],
    'target': qubits[1:] if len(qubits) > 1 else qubits[:1]
  })
  return c

## translation table
_qasm_tbl_ = {
  ## qasm version
  'qasm_version': {
    'default': '2.0',
    'match_order': 0,
    'match_regex': re.compile(r'OPENQASM\s*(.+)\s*;'),
    'to_json': lambda m, _: m.group(1),
    'to_qasm': lambda v: f'OPENQASM {v}'
  },
  ## include file
  'include_files': {
    'default': ['qelib1.inc'],
    'match_order': 10,
    'match_regex': re.compile(r'include\s*"(.+?)"\s*;'),
    'to_json': lambda m, c: list(set(c + [m.group(1)])),
    'to_qasm': lambda v: [f'include "{f}"' for f in v]
  },
  ## number of qubits or classical registers
  'qubits': {
    'default': None,
    'match_order': 30,
    'match_regex': re.compile(r'qreg\s*(?P<name>\w+)\[(?P<num>\d+)\]\s*;'),
    'to_json': lambda m, c: c + [{
      'name': m.group('name'), 'num':  int(m.group('num'))
    }],
    'to_qasm': lambda v: [f'qreg {d["name"]}[{d["num"]}]' for d in v]
  },
  'classical_registers': {
    'default': [],
    'match_order': 30,
    'match_regex': re.compile(r'creg\s*(?P<name>\w+)\[(?P<num>\d+)\]\s*;'),
    'to_json': lambda m, c: c + [{
      'name': m.group('name'), 'num':  int(m.group('num'))
    }],
    'to_qasm': lambda v: [f'creg {d["name"]}[{d["num"]}]' for d in v]
  },
  ## quantum gates
  'quantum_gates': {
    'default': [],
    'match_order': 50,
    'match_regex': re.compile(r'(?P<name>\w+)(\((?P<param>.+?)\))?\s+(?P<qubits>.+?)\s*;'),
    'to_json': lambda m, c: to_json_quantum_gate(m, c),
    'to_qasm': lambda v: [
      ''.join([
        g['name'] + ('' if g['param'] is None else f'({g["param"]})'),
        '' if not g['control'] else ' ',
        ', '.join([f'{c["name"]}[{c["idx"]}]' for c in g['control']]),
        ' ' if not g['control'] else ', ',
        ', '.join([f'{t["name"]}[{t["idx"]}]' for t in g['target']])
      ]) for g in v
    ]
  },
  ## measurement
  'measurements': {
    'default': [],
    'match_order': 40,
    'match_regex': re.compile(
      r'measure\s+(?P<qname>\w+)\[(?P<q>\d+)\]\s*->\s*(?P<cname>\w+)(\[(?P<c>\d+)\])?\s*;'),
    'to_json': lambda m, c: c + [{
      'qubit': {
        'name': m.group('qname'),
        'idx': 0 if m.group('q') is None else int(m.group('q')) 
      },
      'classical_register': {
        'name': m.group('cname'),
        'idx': 0 if m.group('c') is None else int(m.group('c')) 
      }
    }],
    'to_qasm': lambda v: [
      f'measure {m["qubit"]["name"]}[{m["qubit"]["idx"]}]' +
      f' -> {m["classical_register"]["name"]}[{m["classical_register"]["idx"]}]'
      for m in v
    ]
  },
}

## QASM -> JSON
def qasm_to_json(qasm: str) -> str:
  circuit = {
    k: [] if v['default'] is None else v['default']
    for k, v in _qasm_tbl_.items()
  }
  for n, line in enumerate(qasm.splitlines()):
    ## delete comments
    line = line.split('//')[0].strip()
    ## skip empty line
    if not line:
      continue

    tbl = sorted(_qasm_tbl_.items(), key=lambda d: d[1]['match_order'])
    for k, v in tbl:
      if (m := v['match_regex'].fullmatch(line)):
        circuit[k] = v['to_json'](m, circuit[k])
        break
    else:
      print(f'{n+1}: Unknown gate or illegal format: {line}', file=sys.stderr)

  return json.dumps(circuit, indent=2)

## JSON -> QASM
def json_to_qasm(json_str: str) -> Optional[str]:
  circuit = json.loads(json_str)
  qasm = []

  ## translation
  for k, ctx in _qasm_tbl_.items():
    v = circuit[k] if k in circuit and circuit[k] else ctx['default']
    # fatal error
    if v is None:
      print(f'None {k}', file=sys.stderr)
      return None
    ret = ctx['to_qasm'](v)
    qasm += ret if isinstance(ret, list) else [ret]

  return ';\n'.join(qasm) + ';'

if __name__ == '__main__':
  circuit = '''
// example circuit
OPENQASM 2.0;
include "qelib1.inc";

qreg q[2];
creg c0[1];
creg c1[1];

h q[0];
cx q[0], q[1];
rz(pi/2) q[0];
barrier q[1];
measure q[0] -> c0;
measure q[1] -> c1;
'''.strip()

  to_json = qasm_to_json(circuit)
  #print(to_json)
  to_qasm = json_to_qasm(to_json)
  print(to_qasm)
  

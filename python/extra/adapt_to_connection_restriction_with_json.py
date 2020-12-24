##
## 結合制約を満たすための SWAP ゲートを挿入(JSON 形式の量子回路)
##

import json
from qulacs import Graph
from itertools import tee
from typing import List, Tuple, Dict, Iterator

def adapt_to_connection_restriction_with_json(
    json_str: str, qbit_graph: Graph) -> str:

  # utility function
  def pairwise(iterable: List[int]) -> Iterator[Tuple[int, int]]:
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

  rc = test_restriction_with_json(json_str, qbit_graph)
  # return when adaptive
  if len(rc) == 0: return json_str

  circuit = json.loads(json_str)
  gates = circuit['quantum_gates']
  qname = circuit['qubits'][0]['name']
  nc = []
  for i, gate in enumerate(gates):
    if i not in rc: # adaptive gate
      nc.append(gate)
      continue

    # insert swap gates on both sides
    control = [g['idx'] for g in gate['control']]
    target = [g['idx'] for g in gate['target']]
    c, t = control[0], target[0]
    path = _find_shortest_path(qbit_graph, t, c)
    if len(path) == 0: # route not found
      nc.append(gate)
      continue
    path = path[:-1]
    # forward
    [nc.append(_swap_gate(qname, *pair)) for pair in pairwise(path)]
    # change target qubit
    gate['target'][0]['idx'] = path[-1]
    nc.append(gate)
    # backward
    [nc.append(_swap_gate(qname, *pair)) for pair in pairwise(path[::-1])]

  circuit['quantum_gates'] = nc
  return json.dumps(circuit, indent=2)

## 結合制約を検査
def test_restriction_with_json(json_str: str, qbit_graph: Graph) -> List[int]:
  circuit = json.loads(json_str)
  gates = circuit['quantum_gates']
  # there is no constraint graph or no gate in circuit
  if len(qbit_graph) == 0 or len(gates) == 0: return []
  # maximum constraint index is greater than number of qubits of this circuit
  if (circuit['qubits'][0]['num'] - 1) < max(qbit_graph.keys()): return []

  not_adaptive = []
  connections = sum([[(kq, q) for q in vq] for kq, vq in qbit_graph.items()], [])
  for i, gate in enumerate(gates):
    control = [g['idx'] for g in gate['control']]
    target = [g['idx'] for g in gate['target']]
    # skip non-controlled gate(one-qubit gate)
    if len(control) == 0: continue
    if not all(((x, y) in connections for x in control for y in target)):
      not_adaptive.append(i)
  return not_adaptive

# Djikstra's Shortest Path Algorithm
def _find_shortest_path(qbit_graph: Graph, start: int, goal: int) -> List[int]:
  shortest = {start: (None, 0)}
  visited = set()
  cur = start

  while cur != goal:
    visited.add(cur)
    dest = qbit_graph[cur]
    cur_hops = shortest[cur][1]

    for nextq in dest:
      hop = cur_hops + 1
      if nextq not in shortest:
        shortest[nextq] = (cur, hop)
      else:
        cur_shortest = shortest[nextq][1]
        if cur_shortest > hop:
          shortest[nextq] = (cur, hop)

    next_dest = {
      q: shortest[q] for q in shortest if q not in visited
    }
    if not next_dest:
      return [] # route not found
    cur = min(next_dest, key=lambda k: next_dest[k][1])

  path = []
  while cur is not None:
    path.append(cur)
    nextq = shortest[cur][0]
    cur = nextq

  return path[::-1]

# return new swap gate
def _swap_gate(qname: str, a: int, b: int) -> Dict:
  return {
    'name': 'swap', 'param': None,
    'control': [{'name': qname, 'idx': a}], 'target': [{'name': qname, 'idx': b}]
  }

if __name__ == '__main__':
  from qulacs import qasm_to_json, json_to_qasm

  # 量子回路
  qasm = '''
// example circuit
OPENQASM 2.0;
include "qelib1.inc";

qreg q[6];
x q[0];
cx q[0], q[1];
cx q[1], q[2];
cx q[2], q[3];
'''.strip()

  # 量子ビット間の結合を定義
  qbit_graph = {
    0: [1, 2],
    1: [0, 3],
    2: [0, 4],
    3: [1, 5],
    4: [2, 5],
    5: [3, 4]
  }

  json_str = qasm_to_json(qasm)
  result = test_restriction_with_json(json_str, qbit_graph)
  print(result)
  nc = adapt_to_connection_restriction_with_json(json_str, qbit_graph)
  print(json_to_qasm(nc))

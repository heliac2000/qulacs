##
## 結合制約を満たすための SWAP ゲートを挿入
##

from qulacs import add_method, QuantumCircuit
from typing import List, Iterator, Tuple
from itertools import tee
from inspect import getmembers, ismethod

# insert swap gates on both sides
def insert_swap_gate(self) -> QuantumCircuit:
  # utility function
  def pairwise(iterable: List[int]) -> Iterator[Tuple[int, int]]: 
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

  # main
  rc = self.test_restriction()
  # return copy(deepcopy) when adaptive
  if len(rc) == 0: return self.copy()

  nc = QuantumCircuit(self.get_qubit_count())
  for gidx in range(self.get_gate_count()):
    gate = self.get_gate(gidx) # deepcopy
    if gidx not in rc: # adaptive gate
      nc.add_gate(gate)
      continue

    # insert swap gates on both sides
    control_list = gate.get_control_index_list()
    target_list = gate.get_target_index_list()
    if is_SWAP_gate(gate):
      control, target = target_list
    else:
      control, target = control_list[0], target_list[0]
    path = self._find_shortest_path(target, control)
    if len(path) == 0: # route not found
      nc.add_gate(gate)
      continue
    path = path[:-1]
    # forward
    [nc.add_SWAP_gate(*pair) for pair in pairwise(path)]
    f = list(filter(
          lambda m: m[0] == 'add_' + gate.get_name() + '_gate',
          getmembers(nc, predicate=ismethod)))
    if len(f) > 0:
      f[0][1](control, path[-1])
    else:
      pass # ToDo
    # backward
    [nc.add_SWAP_gate(*pair) for pair in pairwise(path[::-1])]

  return nc

# Djikstra's Shortest Path Algorithm
def _find_shortest_path(self, start, goal):
  edge = self.get_qbit_graph()
  shortest = {start: (None, 0)}
  visited = set()
  cur = start
  
  while cur != goal:
    visited.add(cur)
    dest = edge[cur]
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

add_method(QuantumCircuit, insert_swap_gate)
add_method(QuantumCircuit, _find_shortest_path)

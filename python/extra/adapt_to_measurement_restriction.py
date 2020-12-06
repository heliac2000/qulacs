##
## 観測制約を満たすための SWAP ゲートを挿入
##

from qulacs import QuantumCircuit, add_method, is_SWAP_gate
from typing import List, Iterator, Tuple, Union
from itertools import tee
from inspect import getmembers, ismethod

# insert swap gates on both sides
def adapt_to_measurement_restriction(
  self, pos: int) -> Union[QuantumCircuit, None]:
  # utility function
  def pairwise(iterable: List[int]) -> Iterator[Tuple[int, int]]:
    "s -> (s0,s1), (s1,s2), (s2, s3), ..."
    a, b = tee(iterable)
    next(b, None)
    return zip(a, b)

  # check constraint graph
  graph = self.get_qbit_graph()
  # there is no constraint graph
  if len(graph) == 0:
    print('no constraint graph', file=stderr)
    return None
  # no gate in circuit
  if self.get_gate_count() == 0:
    print('no gate in circuit', file=stderr)
    return None
  # maximum constraint index is greater than number of qubits of this circuit
  if (self.get_qubit_count() - 1) < max(graph.keys()):
    print('maximum constraint index is greater than number of qubits', file=stderr)
    return None

  measure = []
  for gate_idx in range(self.get_gate_count()):
    gate = self.get_gate(gate_idx)
    if gate.get_name() == 'Measurement':
      measure.append(gate_idx)

  # None measurement gate
  if not measure: return self.copy()

  # create new circuit
  nc = QuantumCircuit(self.get_qubit_count())
  for gidx in range(self.get_gate_count()):
    gate = self.get_gate(gidx) # deepcopy
    if gidx not in measure:
      nc.add_gate(gate)
      continue

    # insert swap gates
    target = gate.get_target_index_list()[0]
    if target == pos: # same qubit
      nc.add_gate(gate)
      continue
    path = self._find_shortest_path(target, pos)
    if len(path) == 0: # route not found
      nc.add_gate(gate)
      continue
    # forward
    [nc.add_SWAP_gate(*pair) for pair in pairwise(path)]
    # measurement gate
    nc.add_gate(Measurement(pos, gate.get_parameter()[0]))
    # backward
    [nc.add_SWAP_gate(*pair) for pair in pairwise(path[::-1])]

  return nc

add_method(QuantumCircuit, adapt_to_measurement_restriction)

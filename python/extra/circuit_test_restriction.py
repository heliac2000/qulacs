##
## 結合制約を検査
##

from qulacs import QuantumState, QuantumGateBase, QuantumCircuit
from typing import Dict, List

## represent constraint graph
##
Graph = Dict[int, List[int]]

## utility function
##
def add_method(cls, method):
  setattr(cls, method.__name__, method)

## QuantumState.set_qbit_graph(Dict[int, List[int]]) -> None
##
def set_qbit_graph(self, graph: Graph) -> None:
  self._graph = graph
  # get all combination for connection constraints
  self._graph_connections = (
    sum([[(kq, q) for q in vq] for kq, vq in graph.items()], [])
  )

## QuantumState.get_qbit_graph(None) -> Dict[int, List[int]]
##
def get_qbit_graph(self) -> Graph:
  return self._graph if hasattr(self, '_graph') else {}

add_method(QuantumState, set_qbit_graph)
add_method(QuantumState, get_qbit_graph)

## QuantumCircuit.test_restriction(QuantumState) -> List[int]
##
def test_restriction(self, state: QuantumState) -> List[int]:
  graph = state.get_qbit_graph()
  # there is no constraint graph or no gate in circuit
  if len(graph) == 0 or self.get_gate_count() == 0: return []
  # maximum constraint index is greater than number of qubits of this circuit
  if (self.get_qubit_count() - 1) < max(graph.keys()): return []

  not_adaptive = []
  connections = state._graph_connections
  for gate_idx in range(self.get_gate_count()):
    gate = self.get_gate(gate_idx)
    control = gate.get_control_index_list()
    target = gate.get_target_index_list()
    # SWAP gate(no control qubits and two target qubits)
    if gate.get_name() == 'SWAP':
      control.append(target[1])
      target = target[:1]
    # skip non-controlled gate(one-qubit gate)
    if len(control) == 0: continue
    if not all(((x, y) in connections for x in control for y in target)):
      not_adaptive.append(gate_idx)
  return not_adaptive

add_method(QuantumCircuit, test_restriction)

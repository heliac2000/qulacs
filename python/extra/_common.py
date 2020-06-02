##
## Classes and functions
##

from qulacs import QuantumStateBase, QuantumState, QuantumGateBase
from typing import Dict, List, Callable

# represent constraint graph
Graph = Dict[int, List[int]]

# register a instance method
def add_method(cls, method):
  setattr(cls, method.__name__, method)

# SWAP gate ?
def is_SWAP_gate(gate: QuantumGateBase) -> bool:
  return gate.get_name() == 'SWAP'

# QuantumState.set_qbit_graph(Dict[int, List[int]]) -> None
def set_qbit_graph(self, graph: Graph) -> None:
  self._graph = graph
  # get all combination for connection constraints
  self._graph_connections = (
    sum([[(kq, q) for q in vq] for kq, vq in graph.items()], [])
  )

# QuantumState.get_qbit_graph(None) -> Dict[int, List[int]]
def get_qbit_graph(self) -> Graph:
  return self._graph if hasattr(self, '_graph') else {}

add_method(QuantumState, set_qbit_graph)
add_method(QuantumState, get_qbit_graph)

# QuantumState class without state vector
class QuantumEmptyState(QuantumStateBase):
  get_qubit_count: Callable[[QuantumStateBase], int] = lambda self: self._qubit_count
  get_qbit_graph : Callable[[], Graph] = QuantumState.get_qbit_graph
  set_qbit_graph : Callable[[QuantumStateBase, Graph], None] = QuantumState.set_qbit_graph

  def __init__(self, n_qubits: int):
    self._qubit_count = n_qubits


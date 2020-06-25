##
## Classes and functions
##

from qulacs import QuantumGateBase, QuantumCircuit, QuantumState
from math import pi
from typing import Dict, List, Callable

# represent constraint graph
Graph = Dict[int, List[int]]

# register a instance method
def add_method(cls, method):
  setattr(cls, method.__name__, method)

# SWAP gate ?
def is_SWAP_gate(gate: QuantumGateBase) -> bool:
  return gate.get_name() == 'SWAP'

# QuantumCircuit.set_qbit_graph(Dict[int, List[int]]) -> None
def set_qbit_graph(self, graph: Graph) -> None:
  self._graph = graph
  # get all combination for connection constraints
  self._graph_connections = (
    sum([[(kq, q) for q in vq] for kq, vq in graph.items()], [])
  )

# QuantumCircuit.get_qbit_graph(None) -> Dict[int, List[int]]
def get_qbit_graph(self) -> Graph:
  return self._graph if hasattr(self, '_graph') else {}

add_method(QuantumCircuit, set_qbit_graph)
add_method(QuantumCircuit, get_qbit_graph)

# constants
PI, hPI, qPI = pi, pi/2, pi/4

# dictionary class with alias keys
class AliasDict(dict):
  def __init__(self, *args, **kwargs):
    dict.__init__(self, *args, **kwargs)
    self.aliases = {}

  def __getitem__(self, key):
    return dict.__getitem__(self, self.aliases.get(key, key))

  def __setitem__(self, key, value):
    return dict.__setitem__(self, self.aliases.get(key, key), value)

  def __contains__(self, key):
    return (super().__contains__(key)) or (key in self.aliases)

  def keys(self):
    return list(super().keys()) + list(self.aliases)

  def add_alias(self, key, alias):
    self.aliases[alias] = key

# Bloch sphere representation
def qubit_bloch_state(stv: List[float]) -> List[List[float]]:
  from qulacs.gate import Pauli
  import numpy as np

  num = int(np.log2(len(stv)))
  rg = range(num)
  stv = np.asarray(stv)
  stv = np.outer(stv, np.conj(stv))
  bloch_state = []
  # 'I': 0, 'X': 1, 'Y': 2, 'Z': 3
  xyz = np.zeros((num, 3, num), dtype=int)
  for i, v in enumerate(xyz): v[:,i] = [1, 2, 3]
  for i in range(num):
    pauli_singles = [Pauli(rg, p) for p in xyz[i]]
    bloch_state.append(list(
      map(lambda x: np.real(np.trace(np.dot(x.get_matrix(), stv))),
          pauli_singles)))

  return bloch_state

# initialize a qubit with probability amplitude
def initialize_qubit(self: QuantumState, qidx: int, pamp: List[complex]) -> None:
  import inspect
  import numpy as np
  from functools import reduce

  func_name = inspect.currentframe().f_code.co_name
  n = self.get_qubit_count()
  if n < 1:
    print(f'{func_name}: there is no qubits in quantum state', file=stderr)
    return
  elif qidx < 0 or qidx >= n:
    print(f'{func_name}: incorrect qubit index: {qidx}', file=stderr)
    return

  # set |0> state to all qubits
  qubits = np.array([[1, 0]] * n, dtype=complex)
  qubits[qidx] = pamp
  # probability amplitude -> state vector
  stv = reduce(lambda a, b: np.kron(b, a), qubits)
  self.load(stv)
  self.normalize(self.get_squared_norm())

add_method(QuantumState, initialize_qubit)

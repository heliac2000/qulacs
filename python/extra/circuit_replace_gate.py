##
## 基本命令セットの組み合わせによるゲートの置き換え処理
##

from qulacs import QuantumCircuit, QuantumGateBase
from inspect import _signature_get_user_defined_method as _get_method
from math import pi
from sys import stderr
from typing import List, Tuple, Union, Callable

# primitive gate
_primitive_gate = AliasDict({
  # X rotation
  'X-rotation': ['Rx', (0, 1, 1)],
  # Y rotation
  'Y-rotation': ['Ry', (0, 1, 1)],
  # Controlled NOT gate
  'CNOT': ['CNOT', (1, 1, 0)],
  # Swap two qubits
  'SWAP': ['SWAP', (0, 2, 0)],
  # Initialize in state |00..00>
  'INIT': ['', ()],
  # Qubit read out(Measurement)
  'MEAS': ['', ()],
  # Do nothing(Identity gate)
  'NOP' : ['', ()],
  # 量子ドット間電子移動(CCD操作)
  'SHTL': ['', ()]
})

# add alias
for (name, g) in _primitive_gate.items():
  if g[0] and (name != g[0]):
    _primitive_gate.add_alias(name, g[0])

# register primitive gate
def _define_primitive_gate(gate: Tuple[Union[str, Tuple[int]]]) -> Callable:
  if not gate[0]: return lambda: None # none name
  sig = gate[1] # signature
  def _add_gate(
      circuit: QuantumCircuit,
      control: List[int] = [],
       target: List[int] = [],
         args: List[Union[int, float]] = []) -> QuantumGateBase:
    _get_method(circuit, f'add_{gate[0].upper()}_gate')(
      *(control[:sig[0]] + target[:sig[1]] + args[:sig[2]]))
  return _add_gate

# add gate function
for name, g in _primitive_gate.items():
  _add_gate = _define_primitive_gate(g)
  _primitive_gate[name].append(_add_gate)

# compound gate(single qubit operation)
_compound_gate_single_qubit = {
  # Hadamard gate
  'H': [('Ry', qPI), ('Rx', PI), ('Ry', -qPI)],
  # X gate
  'X': [('Rx', PI)],
  # Y gate
  'Y': [('Ry', PI)],
  # Z gate
  'Z': [('Rx', -hPI), ('Ry', PI), ('Rx', hPI)],
  # Phase gate
  'U1': [[('Rx', -hPI), 'Ry', ('Rx', hPI),
          lambda c,t,a: (c,t,(a[2:] if a else a))]],
  # T gate
  'T': [('Rx', -hPI), ('Ry', hPI), ('Rx', hPI)],
  # S gate
  'S': [('Rx', -hPI), ('Ry', qPI), ('Rx', hPI)],
  # Inverse T gate
  'Tdag': [('Rx', -hPI), ('Ry', -hPI), ('Rx', hPI)],
  # Inverse S gate
  'Sdag': [('Rx', -hPI), ('Ry', -qPI), ('Rx', hPI)],
  # Z rotation
  'Z-rotation': [('Rx', -hPI), 'Ry', ('Rx', hPI)],
}

GATE_CNOT = 'CNOT'
GATE_H = _compound_gate_single_qubit['H']
GATE_RZ = _compound_gate_single_qubit['Z-rotation']

# compound gate(two qubitps operation)
_compound_gate_two_qubits = {
  # Controlled Z gate
  'CZ': [GATE_H, GATE_CNOT, GATE_H],
  # Controlled phase gate
  'CR': [
    [GATE_RZ, lambda c,t,a: (c,t,([a[0]/2] if a else a))],  # target
    [GATE_RZ, lambda c,t,a: (t,c,([a[0]/2] if a else a))],  # control
    GATE_CNOT,
    [GATE_RZ, lambda c,t,a: (c,t,([-a[0]/2] if a else a))], # target
    GATE_CNOT
  ],
}

# concatenate
_compound_gate = AliasDict({
  **_compound_gate_single_qubit, **_compound_gate_two_qubits
})

# add alias
_compound_gate.add_alias('Z-rotation', 'Rz')
_compound_gate.add_alias('Tdag', 'Tdagg')
_compound_gate.add_alias('Sdag', 'Sdagg')

# replace
def replace_to_primitive_gates(self: QuantumCircuit) -> QuantumCircuit:
  nc = QuantumCircuit(self.get_qubit_count())
  for gidx in range(self.get_gate_count()):
    gate = self.get_gate(gidx) # deepcopy
    name = gate.get_name()
    # primitive gate or unknown gate
    if name not in _compound_gate:
      nc.add_gate(gate)
      continue
    # compound gate
    def _add_gate(g, control, target, args):
      if isinstance(g, list):
        if g and callable(g[-1]):
          control, target, args = g[-1](control, target, args)
          g = g[:-1]
        [_add_gate(i, control, target, args) for i in g]
        return
      p, *_args = (g if isinstance(g, tuple) else (g,))
      if not _args: _args = args
      if p in _primitive_gate:
        _primitive_gate[p][-1](
          nc, control=control, target=target, args=_args)
      else:
        print(f'unknown primitive gate: {p}', file=stderr)

    control = gate.get_control_index_list()
    target = gate.get_target_index_list()
    args = []
    if _get_method(gate, 'get_parameter'):
      args = gate.get_parameter()
      args = args if isinstance(args, list) else [args]
    for g in _compound_gate[name]:
      _add_gate(g, control, target, args)

  return nc
  
add_method(QuantumCircuit, replace_to_primitive_gates)

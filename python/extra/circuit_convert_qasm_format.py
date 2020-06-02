##
## Convert QuantumCircuit to QASM format
##

from qulacs import QuantumCircuit, add_method, is_SWAP_gate
from sympy import *
from sympy.physics.quantum.qasm import Qasm

def convert_to_qasm_format(self: QuantumCircuit) -> Qasm:
  lines = [f'qubit q_{i}' for i in range(self.get_qubit_count())]
  for gidx in range(self.get_gate_count()):
    gate = self.get_gate(gidx)
    name = gate.get_name().lower()
    control = gate.get_control_index_list()
    target = gate.get_target_index_list()
    if is_SWAP_gate(gate):
      lines.append(f'{name} q_{target[0]}, q_{target[1]}')
    elif len(control) == 0 :
      lines.append(f'{name} q_{target[0]}')
    elif len(control) == 1 and len(target) == 1:
      lines.append(f'{name} q_{control[0]}, q_{target[0]}')

  self._qasm_source = '\n'.join(lines)
  return Qasm(*lines)

add_method(QuantumCircuit, convert_to_qasm_format)

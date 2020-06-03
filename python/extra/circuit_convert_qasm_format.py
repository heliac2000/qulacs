##
## Convert QuantumCircuit to QASM format
##
## Quantum Architectures: qasm2circ
## https://www.media.mit.edu/quanta/qasm2circ/
##
## QASM is a simple text-format language for describing acyclic
## quantum circuits composed from single qubit, multiply controlled
## single-qubit gates, multiple-qubit, and multiple-qubit controlled
## multiple-qubit gates.
##

from qulacs import QuantumCircuit, add_method, is_SWAP_gate

def to_qasm(self: QuantumCircuit) -> str:
  lines = [f'qubit q_{i}' for i in range(self.get_qubit_count())]
  for gidx in range(self.get_gate_count()):
    gate = self.get_gate(gidx)
    name = gate.get_name().lower()
    control = gate.get_control_index_list()
    target = gate.get_target_index_list()
    lc, lt = len(control), len(target)
    if is_SWAP_gate(gate):
      lines.append(f'{name} q_{target[0]}, q_{target[1]}')
    elif lc == 0 and lt == 1:
      lines.append(f'{name} q_{target[0]}')
    elif lc == 1 and lt == 1:
      lines.append(f'{name} q_{control[0]}, q_{target[0]}')
    else:
      pass # ToDo

  return '\n'.join(lines)

add_method(QuantumCircuit, to_qasm)

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

from qulacs import QuantumCircuit, QuantumGateBase, add_method
import re
from sys import stderr
from typing import Union, List, Tuple
from inspect import _signature_get_user_defined_method as _get_method

# classical register
def _cr_func(name: str, control: str, target: str, args: str) -> str:
  ret = f'{name} q{target} -> c{_cr_func.nth}[0];'
  _cr_func.creg.append(f'creg c{_cr_func.nth}[1];')
  _cr_func.nth += 1
  return ret

# transition table
_qasm_trans_tbl = {
  # Hadamard gate
  'H': ['h', (0, 1, 0)],
  # X gate
  'X': ['x', (0, 1, 0)],
  # Y gate
  'Y': ['y', (0, 1, 0)],
  # Z gate
  'Z': ['z', (0, 1, 0)],
  # X rotation
  'X-rotation': ['rx', (0, 1, 1)],
  # Y rotation
  'Y-rotation': ['ry', (0, 1, 1)],
  # Z rotation
  'Z-rotation': ['rz', (0, 1, 1)],
  # Controlled NOT gate
  'CNOT': ['cx', (1, 1, 0)],
  # Controlled Z gate
  'CZ': ['cz', (1, 1, 0)],
  # Controlled phase gate
  'CR': ['cu1', (1, 1, 1)],
  # Swap two qubits
  'SWAP': ['swap', (0, 2, 0)],
  # Phase gate
  'U1': ['u1', (0, 1, -1)],
  # T gate
  'T': ['t', (0, 1, 0)],
  # S gate
  'S': ['s', (0, 1, 0)],
  # Inverse T gate
  'Tdag': ['tdg', (0, 1, 0)],
  # Inverse S gate
  'Sdag': ['sdg', (0, 1, 0)],
  # Identity
  'I': ['id', (0, 1, 0)],
  # Qubit read out
  'Measurement': ['measure', (0, 1, 1), _cr_func],
  # Barrier
  'Separator': [
    'barrier', (0, 2, 0),
    lambda n, c, t, a: f'{n} {",".join([f"q[{i}]" for i in range(t[0], t[1]+1)])};'
  ]
}

# QASM format
def to_qasm(self: QuantumCircuit) -> str:
  # classical register
  _cr_func.nth = 0; _cr_func.creg = []
  code = [
    # header and register
    f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{self.get_qubit_count()}];'
  ]
  for gidx in range(self.get_gate_count()):
    gate = self.get_gate(gidx)
    name = gate.get_name()
    if name not in _qasm_trans_tbl:
      continue
    # 
    g = _qasm_trans_tbl[name]
    f = g[-1] if len(g) > 2 and callable(g[-1]) else None
    name, (nc, nt, nargs) = g[0:2] 
    control = gate.get_control_index_list()
    target = gate.get_target_index_list()
    args = []
    if _get_method(gate, 'get_parameter'):
      args = gate.get_parameter()
      args = args if isinstance(args, list) else [args]
    a = ('' if nargs == 0 else
         f'{args[:nargs][0] if nargs > 0 else args[nargs:][0]}')
    c, t = control[:nc], target[:nt]
    if not f:
      c = ','.join([f'q[{ic}]' for ic in c])
      t = ','.join([f'q[{it}]' for it in t])
    code.append(
      f(name, c, t, a) if f else f'{name}{(a)} {c+"," if c else c}{t};'
    )

  # declare classical register
  if _cr_func.creg:
    code[1:1] = _cr_func.creg

  return '\n'.join(code)

add_method(QuantumCircuit, to_qasm)

# draw circuit on jupyter notebook
def figure(self: QuantumCircuit):
  from qiskit import QuantumCircuit as qiskit_qc
  return qiskit_qc.from_qasm_str(self.to_qasm())

add_method(QuantumCircuit, figure)

# load from QASM code file
def load_qasm(qasm_file: str) -> Union[QuantumCircuit, None]:
  try:
    f = open(qasm_file, 'r')
    lines = f.read().splitlines()
  except OSError:
    print(f'Could not open or read file: {qasm_file}', file=stderr)
    return None
  else:
    f.close()

  # eliminate spaces
  cmd = []
  for line in lines:
    if '#' in line: # comment line
      line = line.split('#')[0]
    line = line.strip() # strip whitespaces
    # empty line
    if len(line) == 0: continue
    cmd.append(line)

  if len(cmd) == 0:
    print(f'No circuit definition in file: {qasm_file}', file=stderr)
    return None

  # find qubit operator
  n_qubits = 0; qubit_tbl = {}
  for i, c in enumerate(cmd):
    match = re.match(r'^qubit\s+(?P<label>[^\s\d]+(?P<idx>\d+))$', c)
    if match is None: continue
    n_qubits += 1
    qubit_tbl[match.group('label')] = int(match.group('idx'))
    cmd[i] = ''

  if n_qubits == 0:
    print(f'No qubit operator in file: {qasm_file}', file=stderr)
    return None

  # remove qubit commands
  cmd = [c for c in cmd if c != '']
  # construct a circuit
  circuit = QuantumCircuit(n_qubits)
  for c in cmd:
    splited = re.split(r'\s+', c)
    if len(splited) < 2:
      print(f'malformed command line: "{c}"', file=stderr)
      return None
    operator, operand = splited[0].replace('-', ''), ''.join(splited[1:])
    if operator == 'nop': continue
    # get method to add a gate
    add_gate_method = _get_method(circuit, f'add_{operator.upper()}_gate')
    if add_gate_method is None:
      print(f'unknown operator: "{operator}" in "{c}"', file=stderr)
      return None
    # convert qubit label to qubit index
    args = []
    for q in re.split(r'[\s,]+', operand):
      if q not in qubit_tbl.keys():
        print(f'unknown qubit: "{q}" in "{c}"', file=stderr)
        return None
      args.append(qubit_tbl[q])
    # signature mismatch ?
    try:
      add_gate_method(*args)
    except TypeError: # ToDo: use inspect.signature or inspect.getfullargspec
      print(f'incompatible operands: "{operand}" in "{c}"', file=stderr)
      return None

  return circuit

# class method
QuantumCircuit.load_qasm = load_qasm

if __name__ == '__main__':
  from qulacs import QuantumState
  from qulacs.gate import Measurement, Identity, Adaptive, X, Z

  from qiskit.visualization.utils import _validate_input_state
  from qiskit.quantum_info.operators.pauli import Pauli
  import numpy as np

  def bloch_multivector(rho):
    rho = _validate_input_state(rho)
    num = int(np.log2(len(rho)))
    bloch_state = []
    for i in range(num):
      pauli_singles = [
        Pauli.pauli_single(num, i, p) for p in ('X', 'Y', 'Z')
      ]
      bloch_state.append(list(
        map(lambda x: np.real(np.trace(np.dot(x.to_matrix(), rho))),
            pauli_singles)))

    return bloch_state

  # construct circuit
  n = 3
  circuit = QuantumCircuit(n)
  circuit.add_H_gate(1);
  circuit.add_CNOT_gate(1, 2);
  circuit.add_CNOT_gate(0, 1);
  circuit.add_H_gate(0);
  circuit.add_Separator(0, 2);
  circuit.add_gate(Measurement(0, 0))
  circuit.add_gate(Measurement(1, 1))
  circuit.add_gate(Adaptive(X(2), lambda cr: cr[0] == 1))
  circuit.add_gate(Adaptive(Z(2), lambda cr: cr[0] == 1))
  circuit.add_CNOT_gate(1, 2);
  circuit.add_CZ_gate(0, 2);

  print(circuit.to_qasm())

  # initialize qubit0
  # state = QuantumState(n)
  # psi = np.random.random(2) + np.random.random(2) * 1j
  # psi = np.append(psi, [0]*(2**n - 2))
  # state.load(psi)
  # state.normalize(state.get_squared_norm())
  # stv0 = state.get_vector()
  # 
  # # update status
  # circuit.update_quantum_state(state)
  # 
  # # result
  # stv1 = state.get_vector()
  # print(stv0)
  # print(stv1)
  # print(bloch_multivector(stv0)[0])
  # print(bloch_multivector(stv1)[-1])

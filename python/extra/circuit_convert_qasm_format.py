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

from qulacs import QuantumCircuit, add_method, is_SWAP_gate, PI
from qiskit import QuantumCircuit as qiskit_qc
import re
from sys import stderr
from typing import Union
from inspect import _signature_get_user_defined_method

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
  'U1': ['u1', (0, 1, 1)],
  # T gate
  'T': ['t', (0, 1, 0)],
  # S gate
  'S': ['s', (0, 1, 0)],
  # Inverse T gate
  'Tdag': ['tdg', (0, 1, 0)],
  # Inverse S gate
  'Sdag': ['sdg', (0, 1, 0)]
}

# QASM format
def to_qasm(self: QuantumCircuit) -> str:
  code = [
    # header and register
    f'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[{self.get_qubit_count()}];'
  ]
  for gidx in range(self.get_gate_count()):
    gate = self.get_gate(gidx)
    name = gate.get_name()
    if name not in _qasm_trans_tbl:
      continue
    name, (nc, nt, nargs) = _qasm_trans_tbl[name][0:2] 
    control = gate.get_control_index_list()
    target = gate.get_target_index_list()
    args = [gate.get_angle()] if hasattr(gate, 'get_angle') else []
    a = '(' + str(args[:nargs][0]) + ')' if nargs > 0 else ''
    c = ','.join([f'q[{c}]' for c in control[:nc]])
    t = ','.join([f'q[{t}]' for t in target[:nt]])
    code.append(f'{name}{a} {c+"," if c else c}{t};')

  return '\n'.join(code)

add_method(QuantumCircuit, to_qasm)

# draw circuit on jupyter notebook
def figure(self: QuantumCircuit):
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
    add_gate_method = _signature_get_user_defined_method(
      circuit, f'add_{operator.upper()}_gate')
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
  circuit = QuantumCircuit(3)
  circuit.add_CR_gate(0, 1, PI)
  print(circuit.to_qasm())
  nc = circuit.replace_to_primitive_gates()
  ##nc.figure()

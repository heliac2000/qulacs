##
## MP-NISQ の MP 部分の方式検討を目的としたシミュレーションを行う機能
##

from qulacs import QuantumState, QuantumCircuit, add_method
from qulacs.gate import Measurement
from typing import List, Callable, Union
from sys import stderr
import inspect

def get_mp_result(
    self: QuantumCircuit, state: QuantumState,
    init: Callable, mp: int) -> List[Union[List[int], List[QuantumState]]]:
  # check initialize function
  if not callable(init):
    print(f'{inspect.currentframe().f_code.co_name}: initialize function is not callable', file=stderr)
    return None

  # prepare a circuit to measure
  n = self.get_qubit_count()
  measure = QuantumCircuit(n)
  for i in range(n):
    measure.add_gate(Measurement(i, n-i-1))

  # tests
  ret1, ret2 = [], []
  for _ in range(mp):
    init(state)
    self.update_quantum_state(state)
    ret2.append(state.get_vector())
    measure.update_quantum_state(state)
    ret1.append([state.get_classical_value(i) for i in range(n)])

  return [ret1, ret2]

add_method(QuantumCircuit, get_mp_result)

if __name__ == '__main__':
  from qulacs import QuantumState, QuantumGateBase, QuantumCircuit, add_method
  from qulacs.gate import Measurement, Identity, Adaptive, X, Z
  from qulacs.gate import BitFlipNoise, TwoQubitDepolarizingNoise
  import numpy as np

  # add noise to a circuit
  def add_noise_to_circuit(
          self: QuantumCircuit,
          single_qubit_noise: QuantumGateBase,
          single_qubit_noise_rate: float,
          two_qubit_noise: QuantumGateBase,
          two_qubit_noise_rate: float) -> QuantumCircuit:
  
    exclude_gate = ('Identity', 'Measurement', 'Separator')
  
    nc = QuantumCircuit(self.get_qubit_count())
      
    for gidx in range(self.get_gate_count()):
      gate = self.get_gate(gidx)
      name = gate.get_name()
      ## Adaptive gate の場合は中身を見る
      if name == 'Adaptive':
        name = gate.get_parameter().get_name()
      ## exclude_gate以外にはノイズをかけない
      if name in exclude_gate:
        nc.add_gate(gate)
      else:
        control = gate.get_control_index_list()
        target = gate.get_target_index_list()
  
        if not control:
          nc.add_gate(gate)
          for ii in range(len(target)): 
            nc.add_gate(single_qubit_noise(target[ii],single_qubit_noise_rate))
        else:
          nc.add_gate(gate)
          nc.add_gate(two_qubit_noise(control[0],target[0],two_qubit_noise_rate))
  
    return nc
  
  add_method(QuantumCircuit,add_noise_to_circuit)

  # initialize function
  def init_state(state: QuantumState) -> None:
    import numpy as np

    if hasattr(init_state, 'init_vector'):
      state.load(init_state.init_vector)
    else:
      ##state.initialize_qubit(1, np.array([1, 0], dtype=complex))
      ##state.initialize_qubit(1, np.random.random(2) + np.random.random(2) * 1j)
      state.initialize_qubit(1, np.array([0.354+0.329j, 0.728+0.437j], dtype=complex))
      # memoize
      init_state.init_vector = state.get_vector()
    return 

  # aggregation
  def aggregate(stv: List[float], ob: List[List[int]], ob_n: List[List[List[int]]]) -> None:
    n_tests, n_qubits = len(ob), len(ob[0])
    stv = np.real(np.multiply(stv, stv.conjugate()))
    label = [f'{i:0{n_qubits}b}' for i in range(2**n_qubits)]
    state = [[int(s) for s in list(l)] for l in label]
    ob_counts = [0]*(2**n_qubits)
    for o in ob: ob_counts[state.index(o)] += 1
    ob_counts_noisy = [[0]*(2**n_qubits) for _ in range(len(ob_n))]
    for nz in zip(*ob_n):
      for i, v in enumerate(nz):
        ob_counts_noisy[i][state.index(v)] += 1
    print(f'{" ":{n_qubits+4}s}state_vector observed observed(noisy)')
    for v in zip(label, stv, ob_counts, *ob_counts_noisy):
      print(f'|{v[0]}>: {v[1]:^12.4f} {v[2]*100/n_tests:>6.2f}%', end=' ')
      for nz in v[3:]:
        print(f'{nz*100/n_tests:>8.2f}%', end=' ')
      print()

  # aggregation(pandas dataframe)
  def aggregate_dataframe(stv: List[float], ob: List[List[int]], ob_n: List[List[List[int]]]) -> List[List[str]]:
    n_tests, n_qubits = len(ob), len(ob[0])
    stv = np.real(np.multiply(stv, stv.conjugate()))
    label = [f'{i:0{n_qubits}b}' for i in range(2**n_qubits)]
    state = [[int(s) for s in list(l)] for l in label]
    ob_counts = [0]*(2**n_qubits)
    for o in ob: ob_counts[state.index(o)] += 1
    ob_counts_noisy = [[0]*(2**n_qubits) for _ in range(len(ob_n))]
    for nz in zip(*ob_n):
      for i, v in enumerate(nz):
        ob_counts_noisy[i][state.index(v)] += 1
    ret = []
    for v in zip(label, stv, ob_counts, *ob_counts_noisy):
      row = [f'|{v[0]}>:', f'{v[1]:6.4f}', f'{v[2]*100/n_tests:>5.2f}%']
      for nz in v[3:]:
        row.append(f'{nz*100/n_tests:>5.2f}%')
      ret.append(row)
    return ret

  # construct circuit - Hadamard test
  n = 2 # num of qubits
  circuit = QuantumCircuit(n)
  circuit.add_H_gate(0);
  circuit.add_CNOT_gate(0, 1);
  circuit.add_H_gate(0);

  # MP result
  state = QuantumState(n)
  num_of_tests = 10000

  # noiseless
  ob_noiseless, stv_noiseless = circuit.get_mp_result(state, init_state, num_of_tests)

  # noisy
  noise = [0.1, 0.2, 0.5, 1.0]
  ob_noisy = []
  for nz in noise:
    noisy_circuit = circuit.add_noise_to_circuit(BitFlipNoise, nz, TwoQubitDepolarizingNoise, nz)
    ob_n, stv_noisy = noisy_circuit.get_mp_result(state, init_state, num_of_tests)
    ob_noisy.append(ob_n)

  # aggregation
  #aggregate(stv_noiseless[0], ob_noiseless, ob_noisy)
  ret = aggregate_dataframe(stv_noiseless[0], ob_noiseless, ob_noisy)

  import pandas as pd
  cols = ['', 'state vector', 'observed'] + [f'Noise rate: {int(nz*100)}%' for nz in noise]
  df = pd.DataFrame(ret, columns=cols)
  print(df)

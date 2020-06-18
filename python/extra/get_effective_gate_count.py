##
## 量子回路内の有効ゲート数をカウント
##

from qulacs import QuantumCircuit, add_method
from typing import Tuple

# 有効ゲート数をカウント
def get_effective_gate_count(
    self: QuantumCircuit,
    # カウントしないゲート種別
    exclude_gate: Tuple[str] = ('Identity', 'Separator', 'Measurement')) -> int:
  # short path
  if not exclude_gate:
    return self.get_gate_count()
  # count
  num_gate = 0
  for gidx in range(self.get_gate_count()):
    gate = self.get_gate(gidx)
    name = gate.get_name()
    # Adaptive gate の場合は中身を見る
    if name == 'Adaptive':
      if name in exclude_gate:
        continue
      else:
        name = gate.get_parameter().get_name()
    if name not in exclude_gate:
      num_gate += 1

  return num_gate

add_method(QuantumCircuit, get_effective_gate_count)

if __name__ == '__main__':
  from qulacs.gate import Measurement, Adaptive, X, Z, Identity

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
  circuit.add_gate(Adaptive(X(2), lambda cr: cr[1] == 1))
  circuit.add_gate(Adaptive(Z(2), lambda cr: cr[0] == 1))
  circuit.add_CNOT_gate(1, 2);
  circuit.add_CZ_gate(0, 2);
  circuit.add_gate(Identity(0))

  # ゲート数
  print(circuit.get_gate_count())
  # 有効ゲート数
  print(circuit.get_effective_gate_count())

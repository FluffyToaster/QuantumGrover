from src.grover.run import *
from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI
import time

start_login = time.time()
enable_account("58957ea5a48a801eb5af6adcae7776126c122c9d")
qi = QuantumInspireAPI()
print("Logged in to QI account ({} seconds)".format(str(time.time() - start_login)[:5]))\

backend = qi.get_backend_type_by_name('QX single-node simulator')

shot_count = 500

# whether to apply optimization to our generated QASM
# performance improvement of ~20-50%
apply_optimization_to_qasm = True

# MODES:
#   - normal: use toffoli gates and ancillary qubits for max speed
#   - no toffoli: same as normal, but replace toffoli gates for 2-gate equivalent circuits. uses ancillary qubits.
#   - crot: no ancillary qubits or toffoli gates, but scales with 3^n gates for n bits
#   - fancy cnot: no ancillary qubits or toffoli gates, scales 2^n
mode = "normal"


# Search example
search_targets = [
    "0110"[::-1],
    "1010"[::-1],
]

qasm, _, qubit_count, data_qubits = generate_search_qasm(search_targets, mode, apply_optimization=apply_optimization_to_qasm)
execute_search_qasm(search_targets, qi, qasm, shot_count, backend, qubit_count, data_qubits, True)


# SAT example
boolean_expr = "(not(a) and not(b) and not(c))"

qasm, _, qubit_count, data_qubits = generate_sat_qasm(boolean_expr, mode, sat_mode="reuse gates", apply_optimization=apply_optimization_to_qasm)
execute_sat_qasm(qi, qasm, shot_count, backend, qubit_count, data_qubits, True)

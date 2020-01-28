from src.grover.run import *
from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI

# smoke test to ensure basic functionality

enable_account("58957ea5a48a801eb5af6adcae7776126c122c9d")
qi = QuantumInspireAPI()
backend = qi.get_backend_type_by_name('QX single-node simulator')
shot_count = 500

cnot_modes = ["normal", "no toffoli", "crot", "fancy cnot"]
sat_modes = ["reuse gates", "reuse qubits"]

# test multi element search for all modes
search_targets = [
    "000100"[::-1],
    "100111"[::-1],
]

for cnot_mode in cnot_modes:
    qasm, _, qubit_count, data_qubits = generate_search_qasm(search_targets, cnot_mode)
    temp, target_probs, non_target_prob, _ = execute_search_qasm(search_targets, qi, qasm, shot_count, backend, qubit_count, data_qubits, plot=False)

    assert non_target_prob < 0.1, "Probability of missing target >0.1 for basic multi element search! (mode {})".format(cnot_mode)
    assert sum(target_probs) + non_target_prob > 0.999, "Total probability not 1, incorrent QASM produced? (mode {})".format(cnot_mode)


# test sat solver for all cnot modes and sat modes
boolean_expr = "(a and b and c and d) or (a and b and not(c) and not(d))"
solutions = {"1111", "1100"}

for cnot_mode in cnot_modes:
    for sat_mode in sat_modes:
        qasm, _, qubit_count, data_qubits = generate_sat_qasm(boolean_expr, cnot_mode, sat_mode=sat_mode)
        suggested_solutions = execute_sat_qasm(qi, qasm, shot_count, backend, qubit_count, data_qubits, plot=False)[1]

        assert set(suggested_solutions) == solutions, "Invalid solution set " \
                                                      "(cnot mode '{}', sat mode '{}')".format(cnot_mode, sat_mode)

print("\n\nAll tests passed!")

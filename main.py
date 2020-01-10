from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI
from functions import *
import math


enable_account("58957ea5a48a801eb5af6adcae7776126c122c9d")
qi = QuantumInspireAPI()

print("Logged in to QI account")

qasm = """

version 1.0

qubits {}

""".format(QUBIT_COUNT)

# initialisation
qasm += fill("H")

# looping grover
iterations = int(math.pi * math.sqrt(2 ** DATA_QUBITS) / 4)
qasm += ".grover_loop({})\n".format(iterations)

# oracle
qasm += oracle()
qasm += toffoli_penis()
qasm += oracle()

# diffusion
qasm += fill("H")
qasm += fill("X")
qasm += toffoli_penis()
qasm += fill("X")
qasm += fill("H")

backend = qi.get_backend_type_by_name('QX single-node simulator')

print(qasm)

print("Executing QASM code ({} instructions, {} qubits, {} shots)".format(qasm.count("\n"), QUBIT_COUNT, SHOT_COUNT))
result = qi.execute_qasm(qasm, backend_type=backend, number_of_shots=SHOT_COUNT)
runtime = result["execution_time_in_seconds"]
print("Ran in {} seconds".format(runtime))

if QUBIT_COUNT > 8:
    print("No plot because of large qubit count")
    histogram_list = interpret_results(result, False)
else:
    histogram_list = interpret_results(result)

for h in histogram_list:
    if h[0] == SEARCH_TARGET[::-1].zfill(QUBIT_COUNT):
        print("Probability of search target: {}".format(h[1]))

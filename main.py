from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI
from functions import *
from optimiser import *
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
iterations = int(math.pi * math.sqrt((2 ** DATA_QUBITS) / len(SEARCH_TARGETS)) / 4)
qasm += ".grover_loop({})\n".format(iterations)

# oracle
for s in range(len(SEARCH_TARGETS)):
    qasm += oracle(SEARCH_TARGETS[s])
    qasm += cnot_pillar()
    qasm += oracle(SEARCH_TARGETS[s])

# diffusion
qasm += fill("H")
qasm += fill("X")
qasm += cnot_pillar()
qasm += fill("X")
qasm += fill("H")

backend = qi.get_backend_type_by_name('QX single-node simulator')
print("Executing QASM code ({} instructions, {} qubits, {} shots)".format(qasm.count("\n"), QUBIT_COUNT, SHOT_COUNT))

if OPTIMISE:
    for i in range(3):
        qasm = optimise(qasm, mode="speed")
    for i in range(6):
        qasm = optimise(qasm, mode="style")
    qasm = clean_code(qasm)
    print(qasm)
    exit()

result = qi.execute_qasm(qasm, backend_type=backend, number_of_shots=SHOT_COUNT)
runtime = result["execution_time_in_seconds"]
print("Ran in {} seconds".format(runtime))

if QUBIT_COUNT > 15:
    print("No plot because of large qubit count")
    histogram_list = interpret_results(result, False)
else:
    histogram_list = interpret_results(result)

for h in histogram_list:
    name, prob = h[0], h[1]
    for s in range(len(SEARCH_TARGETS)):
        if name == SEARCH_TARGET_HEXES[s]:
            print("Probability of search target {}, hex representation '{}': {}".format(s+1,
                                                                                        SEARCH_TARGET_HEXES[s],
                                                                                        prob))

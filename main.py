from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI
from functions import *
from optimiser import *
import math
import time

start_login = time.time()

enable_account("58957ea5a48a801eb5af6adcae7776126c122c9d")
qi = QuantumInspireAPI()
backend = qi.get_backend_type_by_name('QX single-node simulator')

print("Logged in to QI account ({} seconds)".format(str(time.time() - start_login)[:5]))

qasm = """

version 1.0

qubits {}

""".format(QUBIT_COUNT)

start_generate = time.time()

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


if OPTIMISE:
    qasm = apply_optimisations(qasm)

print("Generated QASM in {} seconds".format(str(time.time() - start_generate)[:5]))
print("Executing QASM code ({} instructions, {} qubits, {} shots)".format(qasm.count("\n"), QUBIT_COUNT, SHOT_COUNT))
# print(qasm)
result = qi.execute_qasm(qasm, backend_type=backend, number_of_shots=SHOT_COUNT)
runtime = result["execution_time_in_seconds"]
print("Ran on simulator in {} seconds".format(str(runtime)[:5]))

if QUBIT_COUNT > 15:
    print("No plot because of large qubit count")
    histogram_list = interpret_results(result, False)
else:
    histogram_list = interpret_results(result)

non_target_prob = 0
for h in histogram_list:
    name, prob = h[0], h[1]
    is_target = False
    for s in range(len(SEARCH_TARGETS)):
        if name == SEARCH_TARGET_HEXES[s]:
            is_target = True
            print("Search target {}:".format(s+1))
            print("\tBinary: '{}'".format(SEARCH_TARGETS[s]))
            # print("\tHexadecimal: '{}'".format(SEARCH_TARGET_HEXES[s]))
            print("\tProbability: {}".format(prob))
            print()
    if not is_target:
        non_target_prob += prob

print("Probability of any non-target is {}".format(round(non_target_prob,5)))

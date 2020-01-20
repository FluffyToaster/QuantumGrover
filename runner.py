from functions import *
from optimiser import *
import math
import time


def run_grover(qi, search_targets, shot_count, mode, apply_optimisation=True, plot=False):
    """
    Run a full round of Grover's Algorithm with the given settings.

    Args:
        qi: An instance of the Quantum Inspire API
        search_targets: A list of bit strings to search for
        shot_count: The number of shots to execute on the circuit
        mode: The mode for CNOTs (see main.py)
        apply_optimisation: Whether to apply the optimisation algorithm
        plot: Whether to plot the results of this run

    Returns: A tuple of the following values:
        - histogram_list: a list of pairs, specifying a name and probability, as returned from QI
        - target_probs: The probabilities for each of the targets
        - non_target_prob: The total probability not to find one of the targets
        - line_count: The number of parallel lines of QASM that was executed
        - runtime: The execution time on the QI backend

    """

    search_target_hexes = list(map(lambda s: hex(int(s[::-1], 2))[2:],
                                   search_targets))

    data_qubits = len(search_targets[0])

    if mode in ["crot", "fancy cnot"]:
        ancillary_qubits = 0
    elif mode in ["normal", "no toffoli"]:
        ancillary_qubits = data_qubits - 3
    else:
        raise ValueError("Invalid value for MODE: {}".format(mode))

    qubit_count = data_qubits + ancillary_qubits

    backend = qi.get_backend_type_by_name('QX single-node simulator')

    qasm = "version 1.0\n" \
           "qubits {}\n".format(qubit_count)

    start_generate = time.time()

    # initialisation
    qasm += fill("H", data_qubits)

    # looping grover
    iterations = int(math.pi * math.sqrt((2 ** data_qubits) / len(search_targets)) / 4)
    qasm += ".grover_loop({})\n".format(iterations)

    # oracle
    for s in range(len(search_targets)):
        qasm += oracle(search_targets[s], data_qubits)
        qasm += cnot_pillar(mode, data_qubits)
        qasm += oracle(search_targets[s], data_qubits)

    # diffusion
    qasm += fill("H", data_qubits)
    qasm += fill("X", data_qubits)
    qasm += cnot_pillar(mode, data_qubits)
    qasm += fill("X", data_qubits)
    qasm += fill("H", data_qubits)

    if apply_optimisation:
        qasm = apply_optimisations(qasm, qubit_count, data_qubits)

    # print("Generated QASM in {} seconds".format(str(time.time() - start_generate)[:5]))

    # write_file = open("qasms/latest.qasm", "w")
    # write_file.write(qasm)
    # write_file.close()

    line_count = qasm.count("\n")
    print("Executing QASM code ({} instructions, {} qubits, {} shots)".format(line_count, qubit_count, shot_count))
    result = qi.execute_qasm(qasm, backend_type=backend, number_of_shots=shot_count)
    runtime = result["execution_time_in_seconds"]
    print("Ran on simulator in {} seconds".format(str(runtime)[:5]))

    if qubit_count > 15:
        print("No plot because of large qubit count")
        histogram_list = interpret_results(result, qubit_count, data_qubits, False)
    else:
        histogram_list = interpret_results(result, qubit_count, data_qubits, plot)

    non_target_prob = 0
    target_probs = [0 for _ in range(len(search_targets))]
    for h in histogram_list:
        name, prob = h[0], h[1]
        is_target = False
        for s in range(len(search_targets)):
            if name == search_target_hexes[s]:
                is_target = True
                target_probs[s] = prob
                # print("Search target {}:".format(s + 1))
                # print("\tBinary: '{}'".format(search_targets[s]))
                # print("\tProbability: {}".format(prob))
                # print()
        if not is_target:
            non_target_prob += prob

    # print("Probability of any non-target is {}".format(round(non_target_prob, 5)))

    return histogram_list, target_probs, non_target_prob, line_count, runtime

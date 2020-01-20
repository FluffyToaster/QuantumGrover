from functions import *
from optimiser import *
from sat_generators import *
import math


def run_grover_sat(qi, expr_string, shot_count, mode, apply_optimisation=True, plot=True):
    # backend = qi.get_backend_type_by_name('QX single-node simulator')
    backend = None

    algebra = boolean.BooleanAlgebra()
    expr = algebra.parse(expr_string)

    control_names = list(expr.symbols)

    # note that the number of data qubits also includes an extra bit which must be 1 for the algorithm to succeed
    data_qubits = len(control_names) + 1

    circuit_qasm, _, last_qubit_index = generate_circuit(expr, control_names, True)
    qubit_count = last_qubit_index + 1

    qasm = "version 1.0\n" \
           "qubits {}\n".format(qubit_count)

    # initialisation
    qasm += fill("H", data_qubits)

    # looping grover
    iterations = int(math.pi * math.sqrt(2 ** data_qubits - 1) / 4)
    qasm += ".grover_loop({})\n".format(iterations)

    qasm += circuit_qasm + "\n"

    # diffusion
    qasm += fill("H", data_qubits)
    qasm += fill("X", data_qubits)
    qasm += cnot_pillar(mode, data_qubits)
    qasm += fill("X", data_qubits)
    qasm += fill("H", data_qubits)

    if apply_optimisation:
        qasm = apply_optimisations(qasm, qubit_count, data_qubits)

    return iterations * qasm.count("\n"), qubit_count
    return execute_qasm(qi, qasm, shot_count, backend, qubit_count, data_qubits, plot, False)


def run_grover_search(qi, search_targets, shot_count, mode, apply_optimisation=True, plot=False):
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

    # backend = qi.get_backend_type_by_name('QX single-node simulator')
    backend = None

    qasm = "version 1.0\n" \
           "qubits {}\n".format(qubit_count)

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
    return iterations * qasm.count("\n")
    return execute_qasm(qi, qasm, shot_count, backend, qubit_count, data_qubits, plot, True, search_targets, search_target_hexes)


def execute_qasm(qi, qasm, shot_count, backend, qubit_count, data_qubits, plot, is_search, search_targets=None, search_target_hexes=None):
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

    if is_search:
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

        print("Probability of any non-target is {}".format(round(non_target_prob, 5)))

        return histogram_list, target_probs, non_target_prob, line_count, runtime
    else:
        print(qasm)
        print("Interpreting SAT results:")
        highest_prob = max(map(lambda _: _[1], histogram_list))
        for h in histogram_list:
            name, prob = h[0], h[1]
            if prob > highest_prob / 2:
                print(f"{name} seems to satisfy the formula:")
                bits = bin(int(name, 16))[3:]
                print(bits)

        return histogram_list, -1, -1, line_count, runtime

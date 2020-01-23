from src.grover.qasm_utilities import *
from src.optimizations.optimizer import *
from src.grover.sat_utilities import *
import math


def grover_sat_qasm(expr_string, cnot_mode, sat_mode="fancy", apply_optimization=True):
    """
    Generate the QASM needed to evaluate the SAT problem for a given boolean expression.

    Args:
        expr_string: A boolean expression as a string
        cnot_mode: The mode for CNOTs (see main.py)
        sat_mode: The mode for the SAT solving circuit
        apply_optimization: Whether to apply the optimization algorithm

    Returns: A tuple of the following values:
        - qasm: The QASM representing the requested Grover search
        - line count: The total number of parallel lines that is executed (including grover loops)
        - qubit count: The total number of qubits required
        - data qubits: The number of data qubits
    """

    algebra = boolean.BooleanAlgebra()
    expr = algebra.parse(expr_string)

    control_names = sorted(list(expr.symbols), reverse=True)

    # note that the number of data qubits also includes an extra bit which must be 1 for the algorithm to succeed
    data_qubits = len(control_names) + 1

    expr = split_expression_evenly(expr)

    if sat_mode == "normal":
        oracle_qasm, _, last_qubit_index = generate_sat_oracle(expr, control_names, is_toplevel=True)
    elif sat_mode == "fancy":
        _, oracle_qasm, last_qubit_index = generate_fancy_sat_oracle(expr, [], control_names, is_toplevel=True)
    else:
        raise ValueError("Invalid SAT mode: {} instead of 'normal' or 'fancy'".format(sat_mode))

    qubit_count = last_qubit_index + 1

    # some modes may require many ancillary qubits for the diffusion operator!
    if cnot_mode in ["normal", "no toffoli"]:
        qubit_count = max(qubit_count, data_qubits * 2 - 3)

    qasm = "version 1.0\n" \
           "qubits {}\n".format(qubit_count)

    # initialisation
    qasm += fill("H", data_qubits)

    # looping grover
    iterations = int(math.pi * math.sqrt(2 ** data_qubits - 1) / 4)
    qasm += ".grover_loop({})\n".format(iterations)

    qasm += oracle_qasm + "\n"

    # diffusion
    qasm += fill("H", data_qubits)
    qasm += fill("X", data_qubits)
    qasm += cnot_pillar(cnot_mode, data_qubits)
    qasm += fill("X", data_qubits)
    qasm += fill("H", data_qubits)

    if apply_optimization:
        qasm = apply_optimizations(qasm, qubit_count, data_qubits)

    return qasm, iterations * qasm.count("\n"), qubit_count, data_qubits


def grover_search_qasm(search_targets, mode, apply_optimization=True):
    """
    Generate the QASM needed to perform an unordered search using Grover's Algorithm.

    Args:
        search_targets: A list of bit strings to search for
        mode: The mode for CNOTs (see main.py)
        apply_optimization: Whether to apply the optimization algorithm

    Returns: A tuple of the following values:
        - qasm: The QASM representing the requested Grover search
        - line count: The total number of parallel lines that is executed (including grover loops)
        - qubit count: The total number of qubits required
        - data qubits: The number of data qubits
    """

    data_qubits = len(search_targets[0])

    if mode in ["crot", "fancy cnot"]:
        ancillary_qubits = 0
    elif mode in ["normal", "no toffoli"]:
        ancillary_qubits = data_qubits - 3
    else:
        raise ValueError("Invalid value for MODE: {}".format(mode))

    qubit_count = data_qubits + ancillary_qubits

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

    if apply_optimization:
        qasm = apply_optimizations(qasm, qubit_count, data_qubits)

    return qasm, iterations * qasm.count("\n"), qubit_count, data_qubits


def execute_search_qasm(search_targets, qi, qasm, shot_count, backend, qubit_count, data_qubits, plot):
    """
    Execute the given QASM code and parse the results as though we are running an unordered search.

    Args:
        search_targets: A list of bit strings to search for
        qi: An instance of the Quantum Inspire API
        qasm:
        shot_count: The number of shots to execute on the circuit
        backend:
        qubit_count:
        data_qubits:
        plot: Whether to plot the results of this run

    Returns: A tuple of the following values:
        - histogram_list: a list of pairs, specifying a name and probability, as returned from QI
        - target_probs: The probabilities for each of the targets
        - non_target_prob: The total probability not to find one of the targets
        - runtime: The execution time on the QI backend
    """

    print("Executing QASM code ({} qubits, {} shots)".format(qubit_count, shot_count))
    result = qi.execute_qasm(qasm, backend_type=backend, number_of_shots=shot_count)
    runtime = result["execution_time_in_seconds"]
    print("Ran on simulator in {} seconds".format(str(runtime)[:5]))

    if qubit_count > 15:
        print("No plot because of large qubit count")
        histogram_list = interpret_results(result, qubit_count, data_qubits, False)
    else:
        histogram_list = interpret_results(result, qubit_count, data_qubits, plot)

    search_target_hexes = list(map(lambda s: hex(int(s[::-1], 2))[2:],
                                   search_targets))

    non_target_prob = 0
    target_probs = [0 for _ in range(len(search_targets))]
    for h in histogram_list:
        name, prob = h[0], h[1]
        is_target = False
        for s in range(len(search_targets)):
            if name == search_target_hexes[s]:
                is_target = True
                target_probs[s] = prob
                print("Search target {}:".format(s + 1))
                print("\tBinary: '{}'".format(search_targets[s]))
                print("\tProbability: {}".format(prob))
                print()
        if not is_target:
            non_target_prob += prob

    print("Probability of any non-target is {}".format(round(non_target_prob, 5)))

    return histogram_list, target_probs, non_target_prob, runtime


def execute_sat_qasm(qi, qasm, shot_count, backend, qubit_count, data_qubits, plot):
    """
    Execute the given QASM code and parse the results as though we are evaluating the SAT problem.

    Args:
        qi:
        qasm:
        shot_count:
        backend:
        qubit_count:
        data_qubits:
        plot:

    Returns: A tuple of the following values:
        - histogram_list: a list of pairs, specifying a name and probability, as returned from QI
        - runtime: The execution time on the QI backend
    """

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

    print("Interpreting SAT results:")
    highest_prob = max(map(lambda _: _[1], histogram_list))
    for h in histogram_list:
        name, prob = h[0], h[1]
        if prob > highest_prob / 2:
            bits = bin(int(name, 16))[3:]
            print("{} seems to satisfy the formula:".format(bits))

    return histogram_list, runtime


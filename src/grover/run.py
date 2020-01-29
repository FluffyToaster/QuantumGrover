from src.grover.search_utilities import *
from src.grover.sat_utilities import *
from src.optimizations.optimizer import *
import math


def generate_search_qasm(search_targets, mode, apply_optimization=True):
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
        qasm += search_oracle(search_targets[s], data_qubits)
        qasm += cnot_pillar(mode, data_qubits)
        qasm += search_oracle(search_targets[s], data_qubits)

    # diffusion
    qasm += fill("H", data_qubits)
    qasm += fill("X", data_qubits)
    qasm += cnot_pillar(mode, data_qubits)
    qasm += fill("X", data_qubits)
    qasm += fill("H", data_qubits)

    if mode != "no toffoli":
        if apply_optimization:
            qasm = apply_optimizations(qasm, qubit_count, data_qubits)

    elif mode == "no toffoli":
        if apply_optimization:
            qasm = optimize_toffoli(qasm)

        # replace toffoli gates at the last minute, after optimisation, to ensure smallest circuit
        qasm = replace_toffoli_with_alt(qasm)

        if apply_optimization:
            qasm = apply_optimizations(qasm, qubit_count, data_qubits)

    return qasm, iterations * qasm.count("\n"), qubit_count, data_qubits


def execute_search_qasm(search_targets, qi, qasm, shot_count, backend, qubit_count, data_qubits, plot):
    """
    Execute the given QASM code and parse the results as though we are running an unordered search.

    Args:
        search_targets: A list of bit strings to search for
        qi: An instance of the Quantum Inspire API
        qasm: The qasm program
        shot_count: The number of shots to execute on the circuit
        backend: An instance a QI API backend
        qubit_count: The total number of qubits used in the qasm program
        data_qubits: The number of qubits used by Grover's Algorithm (aka non-ancillary)
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

    non_target_prob = 0
    target_probs = [0 for _ in range(len(search_targets))]
    for h in histogram_list:
        name, prob = h[0], h[1]
        is_target = False
        for s in range(len(search_targets)):
            # the bit string should have leading zeroes
            if name == "0" * (qubit_count - data_qubits) + search_targets[s][::-1]:
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


def generate_sat_qasm(expr_string, cnot_mode, sat_mode, apply_optimization=True):
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

    expr = split_expression_evenly(expr.simplify())

    if sat_mode == "reuse gates":
        oracle_qasm, _, last_qubit_index = generate_sat_oracle_reuse_gates(expr, control_names, is_toplevel=True)
    elif sat_mode == "reuse qubits":
        oracle_qasm, _, last_qubit_index = generate_sat_oracle_reuse_qubits(expr, control_names, [], is_toplevel=True)
    else:
        raise ValueError("Invalid SAT mode: {} instead of 'reuse gates' or 'reuse qubits'".format(sat_mode))

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


def execute_sat_qasm(qi, qasm, shot_count, backend, qubit_count, data_qubits, plot):
    """
    Execute the given QASM code and parse the results as though we are evaluating a SAT problem.

    Args:
        qi: An instance of the Quantum Inspire API
        qasm: The qasm program
        shot_count: The number of shots to execute on the circuit
        backend: An instance a QI API backend
        qubit_count: The total number of qubits used in the qasm program
        data_qubits: The number of qubits used by Grover's Algorithm (aka non-ancillary)
        plot: Whether to plot the results of this run

    Returns: A tuple of the following values:
        - histogram_list: a list of pairs, specifying a name and probability, as returned from QI
        - likely_solutions: a list of bit strings, all of which seem to solve the given formula, according to grover
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

    likely_solutions = []
    print("Interpreting SAT results:")
    highest_prob = max(map(lambda _: _[1], histogram_list))
    for h in histogram_list:
        # remove all ancillaries and the lowest order data bit: in SAT this is always 1
        name, prob = h[0][-data_qubits+1:], h[1]
        if prob > highest_prob / 2:
            print("{} seems to satisfy the formula:".format(name))
            likely_solutions.append(name)

    return histogram_list, likely_solutions, runtime

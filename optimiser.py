from settings import *
# from bruteforcer import *
# optimisations = generate_optimisation_dict()

optimisations = {
    "HXH": "Z",
    "HH": "",
    "XX": "",
    "ZX": "Y"
}
largest_opt = 3


def apply_optimisations(qasm):
    """
    Apply 3 types of optimisation to the given QASM code:
        Combine groups of gates, such as H-X-H, to faster equivalent gates, Z in this case.
        Shift gates to be executed in parallel.
        Clean QASM code itself (q[1,2,3] becomes q[1:3])

    Args:
        qasm: Valid QASM code to optimise

    Returns: A _equivalent_ piece of QASM with optimisations applied
    """

    # run "speed" mode until QASM does not change
    prev_qasm = ""
    while prev_qasm != qasm:
        prev_qasm = qasm[:]
        qasm = optimise(qasm, mode="speed")

    # run "style" mode until QASM does not change
    prev_qasm = ""
    while prev_qasm != qasm:
        prev_qasm = qasm[:]
        qasm = optimise(qasm, mode="style")

    # tidy up "ugly" optimised code
    qasm = clean_code(qasm)

    return qasm


def remove_gate_from_line(local_qasm_line, gate_symbol, qubit_index):
    """
    Removes the application of a specific gate on a specific qubit.

    Args:
        local_qasm_line: The line from which this call should be removed.
        gate_symbol: The symbol representing the gate
        qubit_index: The index of the target qubit

    Returns: The same line of QASM, with the gate removed.
    """

    # if gate applied to single qubit, remove gate call entirely
    single_application = "{} q[{}]".format(gate_symbol, qubit_index)
    if single_application in local_qasm_line:
        # if there is a parallel bar right
        local_qasm_line = local_qasm_line.replace(single_application + " | ", "")
        # else: if there is a parallel bar left
        local_qasm_line = local_qasm_line.replace(" | " + single_application, "")
        # else: if it is not parellelized at all
        local_qasm_line = local_qasm_line.replace(single_application, "")

    # else remove just the number
    else:
        local_qasm_line = local_qasm_line.replace(",{}".format(qubit_index), "")
        local_qasm_line = local_qasm_line.replace("{},".format(qubit_index), "")

    return local_qasm_line


def add_gate_to_line(local_qasm_line, gate_symbol, qubit_index):
    """
    Add in parallel the application of a gate on a qubit.
    Args:
        local_qasm_line: The existing line of QASM to add the gate in.
        gate_symbol: The symbol representing the gate.
        qubit_index: The index of the target qubit.

    Returns: The same line of QASM with the gate added.
    """

    # if another operation is already called on this qubit, we have to put the new gate on a new line
    # TODO investigate if this breaks for QUBIT_COUNT > 9?
    if str(qubit_index) in local_qasm_line:
        local_qasm_line += "\n{} q[{}]\n".format(gate_symbol, qubit_index)

    # if the line is not empty, we need to consider what's already present
    elif local_qasm_line != "":
        # a bracket indicates this line is parallelized with the { gate | gate | gate } syntax
        if "{" in local_qasm_line:
            # remove } from the line and add it back at the end
            local_qasm_line = local_qasm_line.rstrip("}\n") + \
                              " | " + \
                              "{} q[{}]".format(gate_symbol, qubit_index) + \
                              "}\n"

        # no bracket means we have to add the parallelization syntax ourselves
        else:
            local_qasm_line = "{" + local_qasm_line.rstrip("\n") + \
                              " | " + \
                              "{} q[{}]".format(gate_symbol, qubit_index) + "}\n"

    # else, if the line IS empty, we can just put this gate in directly
    else:
        local_qasm_line = "{} q[{}]\n".format(gate_symbol, qubit_index)
    return local_qasm_line


def optimise(qasm, mode="speed"):
    """
    Apply a single pass of performance-oriented optimisations to the given QASM.

    Args:
        qasm: A valid QASM program to optimise.
        mode: Setting that determines the type of optimisation:
            "speed" -> combine gates into equivalent smaller gates
            "style" -> parallelize gates for speedup and aesthetics

    Returns: Functionally the same QASM code, with one run of optimisations applied.
    """

    qasm_lines = qasm.split("\n")
    gates_applied = []
    for i in range(QUBIT_COUNT):
        gates_applied.append([])

    for q in range(len(qasm_lines)):
        line = qasm_lines[q]
        if len(line) == 0:
            continue

        gate = line.split()[0].lstrip("{")
        if gate not in ["H", "X", "Y", "Z"]:
            gate = "_"

        if "[" in line:
            if "Toffoli" not in line:
                qubit_string = line[line.index("[") + 1:line.index("]")]
                if ":" in qubit_string:
                    affected_qubits = list(range(int(qubit_string.split(":")[0]),
                                                 int(qubit_string.split(":")[1]) + 1))
                elif "," in qubit_string:
                    affected_qubits = list(map(int, qubit_string.split(",")))
                else:
                    affected_qubits = [int(qubit_string)]
            else:
                qs = line.split()[1].split(",")
                affected_qubits = map(lambda x: int(x[2]), qs)

            for a in affected_qubits:
                gates_applied[a].append((q, gate))
        else:
            for a in range(DATA_QUBITS):
                gates_applied[a].append((q, gate))

    for qubit in range(len(gates_applied)):
        gates = gates_applied[qubit]
        skip_counter = 0
        for g in range(len(gates)):
            if skip_counter > 0:
                skip_counter -= 1
                continue

            if mode == "speed":
                for offset in range(0, largest_opt - 1):
                    next_gates = "".join(map(lambda _: _[1], gates[g:g+largest_opt-offset]))
                    if next_gates in optimisations:
                        replacement = optimisations[next_gates]

                        line_indices = list(map(lambda _: _[0], gates[g:g+largest_opt-offset]))
                        # first, remove all gates that are to be replaced
                        for idx, line_number in enumerate(line_indices):
                            qasm_lines[line_number] = remove_gate_from_line(qasm_lines[line_number],
                                                                            next_gates[idx],
                                                                            qubit)

                        # add replacement gate to first line index
                        # unless there is no replacement gate, of course
                        if replacement != "":
                            qasm_lines[line_indices[0]] = add_gate_to_line(qasm_lines[line_indices[0]],
                                                                           replacement,
                                                                           qubit)

                        # ensure we skip a few gates
                        skip_counter += len(next_gates) - 1

            elif mode == "style":
                # check if we can shift left to align with other gates
                current_line, current_gate = gates[g]
                prev_line = current_line - 1

                # we obviously can't shift a toffoli control
                if "Toffoli" in qasm_lines[current_line]:
                    continue

                # if previous line has a Toffoli bar, don't parellelize for style purposes
                if "Toffoli" in qasm_lines[prev_line]:
                    continue

                # if this or the previous line has a break statement, no shifting possible
                if current_gate == "_" or (gates[g - 1][1] == "_" and gates[g - 1][0] == prev_line):
                    continue

                if qasm_lines[prev_line] == "":
                    continue

                # having passed these checks, we can try to actually shift
                if current_gate in ["H", "X", "Y", "Z"] and str(qubit) not in qasm_lines[prev_line]:
                    # remove from current line
                    qasm_lines[current_line] = remove_gate_from_line(qasm_lines[current_line], current_gate, qubit)

                    # add to left
                    qasm_lines[prev_line] = add_gate_to_line(qasm_lines[prev_line], current_gate, qubit)

    # remove blank lines
    qasm_lines = list(filter(lambda x: x not in ["", "{}", " "], qasm_lines))
    return "\n".join(qasm_lines).replace("\n\n", "\n")


def clean_code(qasm):
    """
    Clean given QASM by rewriting each line to a more readable format.
    For example, "{ X q[0] | H q[3,4,5] | X q[1] | X q[2] }"
    Would become "{ X q[0:2] | H q[3:5]"

    Args:
        qasm: Valid QASM code to clean

    Returns: The same QASM code with improved formatting.
    """

    qasm_lines = qasm.split("\n")
    for idx in range(len(qasm_lines)):
        line = qasm_lines[idx]
        gate_dict = {}
        new_line = ""
        if "Toffoli" not in line and ("{" in line or "," in line):
            line = line.strip("{}")
            elements = line.split("|")
            for e in elements:
                gate, target = e.split()
                indices = list(map(int, target.strip("q[]").split(",")))
                if gate not in gate_dict:
                    gate_dict[gate] = indices
                else:
                    gate_dict[gate] += indices

            parallel = len(gate_dict.keys()) > 1
            if parallel:
                new_line += "{ "
            for gate, indices in gate_dict.items():
                if max(indices) - min(indices) + 1 == len(indices) > 1:
                    new_line += "{} q[{}:{}]".format(gate, min(indices), max(indices))
                else:
                    new_line += "{} q[{}]".format(gate, ",".join(map(str, indices)))
                new_line += " | "

            new_line = new_line[:-3]
            if parallel:
                new_line += " }"
        else:
            new_line = line

        qasm_lines[idx] = new_line

    return "\n".join(qasm_lines)

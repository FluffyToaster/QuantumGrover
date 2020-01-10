from settings import *
import time

optimisations = {
    "HXH": "Z",
    "HH": "",
    "XX": "",
    "ZX": "Y"
}
largest_opt = 3


def optimise(qasm):
    start = time.time_ns()
    qasm_lines = qasm.split("\n")
    gates_applied = []
    for i in range(QUBIT_COUNT):
        gates_applied.append([])

    for q in range(len(qasm_lines)):
        line = qasm_lines[q]
        if len(line) == 0:
            continue

        gate = line.split()[0]
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

            for offset in range(0, largest_opt - 1):
                next_gates = "".join(map(lambda _: _[1], gates[g:g+largest_opt-offset]))
                if next_gates in optimisations:
                    opt = optimisations[next_gates]
                    # add optimised gate, remove original line references
                    line_indices = list(map(lambda _: _[0], gates[g:g+largest_opt-offset]))
                    print("Optimising {} for {} on lines {}".format(next_gates, opt, line_indices))

                    for l in line_indices:
                        edit_line = qasm_lines[l]
                        if "," not in edit_line:
                            # if gate applied to single qubit, remove altogether
                            edit_line = ""
                        else:
                            # remove number
                            edit_line = edit_line.replace("{}".format(qubit), "")
                            # fix loose commas
                            edit_line = edit_line.replace(",,", ",")
                            edit_line = edit_line.replace(",]", "]")
                            edit_line = edit_line.replace("[,", "[")

                        qasm_lines[l] = edit_line

                    # add replacement gate to first line index
                    # unless there is no replacement gate, of course
                    if opt != "":
                        if qasm_lines[line_indices[0]] != "":
                            qasm_lines[line_indices[0]] = "{" + qasm_lines[line_indices[0]] + " | " + "{} q[{}]".format(opt, qubit) + "}\n"
                        else:
                            qasm_lines[line_indices[0]] += "{} q[{}]".format(opt, qubit)

                    # ensure we skip a few gates
                    skip_counter += len(next_gates) - 1

            # check if we can shift left to align with other gates
            current_line, current_gate = gates[g]
            prev_line = current_line - 1
            if current_gate in ["H", "X", "Y", "Z"] \
                    and str(qubit) not in qasm_lines[prev_line]:
                # remove from current line
                edit_line = qasm_lines[current_line]
                if "{} q[{}]" in edit_line:
                    # if gate applied to single qubit, remove altogether
                    edit_line = edit_line.replace("{} q[{}] | ".format(current_gate, qubit), "")
                    edit_line = edit_line.replace(" | {} q[{}]".format(current_gate, qubit), "")
                else:
                    # remove number
                    edit_line = edit_line.replace(",{}".format(qubit), "")
                    edit_line = edit_line.replace("{},".format(qubit), "")

                qasm_lines[current_line] = edit_line

                # add to left
                if qasm_lines[prev_line] != "":
                    if "{" not in qasm_lines[prev_line]:
                        qasm_lines[prev_line] = "{" + qasm_lines[prev_line].replace("\n", "") + \
                                                       " | " + \
                                                       "{} q[{}]".format(current_gate, qubit) + "}\n"
                    else:
                        qasm_lines[prev_line] = qasm_lines[prev_line].replace("}\n", "") + \
                                                " | " + \
                                                "{} q[{}]".format(current_gate, qubit) + "}\n"
                else:
                    qasm_lines[prev_line] = "{} q[{}]\n".format(current_gate, qubit)



    end = time.time_ns()
    print("Optimised in {} ms".format((end - start) / 1000000))
    return "\n".join(qasm_lines)

import boolean
from boolean.boolean import AND, OR, NOT, Symbol


def generate_circuit(expr: boolean.Expression, control_names, is_toplevel=False):
    global global_last_ancillary_index
    if is_toplevel:
        global_last_ancillary_index = len(control_names)
    # returns qasm and qubit line of output

    local_qasm = ""

    # go through possible types
    if type(expr) == AND or type(expr) == OR:
        # left side
        left_qasm, left_qubit= generate_circuit(expr.args[0], control_names)
        right_qasm, right_qubit = generate_circuit(expr.args[1], control_names)
        local_qasm += left_qasm
        local_qasm += right_qasm
    elif type(expr) == NOT:
        inner_qasm, inner_qubit = generate_circuit(expr.args[0], control_names)
        local_qasm += inner_qasm
        local_qasm += f"X q[{inner_qubit}]\n"
        return local_qasm, inner_qubit
    elif type(expr) == Symbol:
        # nothing to do here
        return local_qasm, control_names.index(expr)
    else:
        raise ValueError(f"Unknown boolean expr type: {type(expr)}")

    if is_toplevel:
        target_qubit = len(control_names)
        local_qasm += f"H q[{len(control_names)}]\n"
        left_half_qasm = local_qasm[:]
    else:
        # we need another ancillary bit
        global_last_ancillary_index += 1
        target_qubit = global_last_ancillary_index

    if type(expr) == AND:
        local_qasm += generate_and(left_qubit, right_qubit, target_qubit)
    elif type(expr) == OR:
        local_qasm += generate_or(left_qubit, right_qubit, target_qubit)

    # undo NOT applications
    if len(expr.args) == 2 and not is_toplevel:
        if type(expr.args[0]) == NOT:
            local_qasm += f"X q[{left_qubit}]\n"
        if type(expr.args[1]) == NOT:
            local_qasm += f"X q[{right_qubit}]\n"

    if is_toplevel:
        local_qasm += "\n".join(left_half_qasm.split("\n")[::-1])
        return local_qasm, target_qubit, global_last_ancillary_index

    return local_qasm, target_qubit


def generate_and(qubit_1, qubit_2, target_qubit):
    # returns qasm
    return f"Toffoli q[{qubit_1}],q[{qubit_2}],q[{target_qubit}]\n"


def generate_or(qubit_1, qubit_2, target_qubit):
    local_qasm = f"X q[{qubit_1},{qubit_2}]\n"
    local_qasm += f"Toffoli q[{qubit_1}],q[{qubit_2}],q[{target_qubit}]\n"
    local_qasm += f"X q[{qubit_1},{qubit_2},{target_qubit}]\n"
    return local_qasm

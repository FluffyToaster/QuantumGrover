import boolean
from boolean.boolean import AND, OR, NOT, Symbol
import random


def generate_sat_oracle(expr: boolean.Expression, control_names, is_toplevel=False):
    """
    Generate the circuit needed for an oracle solving the SAT problem, given a boolean expression.

    Args:
        expr: The boolean expression (instance of boolean.Expression, not a string)
        control_names: The names of the control variables
        is_toplevel: Whether this is the main call, or a recursive call

    Returns: QASM representing a SAT oracle
    """

    global global_last_ancillary_index
    if is_toplevel:
        global_last_ancillary_index = len(control_names)
    local_qasm = ""

    # go through possible types
    if type(expr) == AND or type(expr) == OR:
        # left side
        left_qasm, left_qubit= generate_sat_oracle(expr.args[0], control_names)
        right_qasm, right_qubit = generate_sat_oracle(expr.args[1], control_names)
        local_qasm += left_qasm
        local_qasm += right_qasm
    elif type(expr) == NOT:
        inner_qasm, inner_qubit = generate_sat_oracle(expr.args[0], control_names)
        local_qasm += inner_qasm
        local_qasm += "X q[{}]\n".format(inner_qubit)
        return local_qasm, inner_qubit
    elif type(expr) == Symbol:
        # nothing to do here
        return local_qasm, control_names.index(expr)
    else:
        raise ValueError("Unknown boolean expr type: {}".format(type(expr)))

    if is_toplevel:
        target_qubit = len(control_names)
        local_qasm += "H q[{}]\n".format(len(control_names))
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
            local_qasm += "X q[{}]\n".format(left_qubit)
        if type(expr.args[1]) == NOT:
            local_qasm += "X q[{}]\n".format(right_qubit)

    if is_toplevel:
        local_qasm += "\n".join(left_half_qasm.split("\n")[::-1])
        return local_qasm, target_qubit, global_last_ancillary_index

    return local_qasm, target_qubit


def generate_and(qubit_1, qubit_2, target_qubit):
    return "Toffoli q[{}],q[{}],q[{}]\n".format(qubit_1, qubit_2, target_qubit)


def generate_or(qubit_1, qubit_2, target_qubit):
    local_qasm = "X q[{},{}]\n".format(qubit_1, qubit_2)
    local_qasm += generate_and(qubit_1, qubit_2, target_qubit)
    local_qasm += "X q[{},{},{}]\n".format(qubit_1, qubit_2, target_qubit)
    return local_qasm


def split_expression_evenly(expr):
    expr_type = type(expr)
    if len(expr.args) > 2:
        halfway = int(len(expr.args) / 2)
        right_expanded = split_expression_evenly(expr_type(*expr.args[halfway:]))

        if len(expr.args) > 3:
            left_expanded = split_expression_evenly(expr_type(*expr.args[:halfway]))
        else:
            left_expanded = split_expression_evenly(expr.args[0])

        return expr_type(left_expanded, right_expanded)
    elif len(expr.args) == 2:
        return expr_type(split_expression_evenly(expr.args[0]),
                         split_expression_evenly(expr.args[1]))
    else:
        return expr


def generate_fancy_sat_oracle(expr, avoid, control_names, last_qubit=-1, is_toplevel=False):
    first_ancillary_bit = len(control_names) + 1

    if len(expr.args) > 2:
        raise ValueError("Fancy SAT Oracle expects only 1 and 2-argument expressions, but got {}".format(expr.args))

    if type(expr) == Symbol:
        return control_names.index(expr), "", last_qubit
    elif type(expr) == NOT:
        qubit_index = control_names.index(expr.args[0])
        return qubit_index, "X q[{}]".format(qubit_index), last_qubit
    elif type(expr) == AND:
        generate_func = generate_and
    elif type(expr) == OR:
        generate_func = generate_or
    else:
        raise ValueError("Unknown type in Boolean expression: {}".format(type(expr)))

    left_expr = expr.args[0]
    right_expr = expr.args[1]

    left_line, left_qasm, left_last_qubit = generate_fancy_sat_oracle(left_expr, avoid[:], control_names, last_qubit)
    avoid.append(left_line)
    right_line, right_qasm, right_last_qubit = generate_fancy_sat_oracle(right_expr, avoid[:], control_names, last_qubit)
    avoid.append(right_line)

    target_line = -1
    # if toplevel, we know what to target
    if is_toplevel:
        target_line = first_ancillary_bit - 1
        my_qasm = "H q[{}]\n".format(target_line) + \
                  generate_func(left_line, right_line, target_line) + \
                  "H q[{}]\n".format(target_line)
    else:
        # find the lowest line we can use
        for i in range(first_ancillary_bit, first_ancillary_bit + max(avoid) + 1):
            if i not in avoid:
                target_line = i
                break
        my_qasm = generate_func(left_line, right_line, target_line)

    last_qubit = max(last_qubit, max(avoid), left_last_qubit, right_last_qubit, target_line)

    qasm = "\n".join([
        left_qasm,
        right_qasm,
        my_qasm,
        *right_qasm.split("\n")[::-1],
        *left_qasm.split("\n")[::-1]
    ])

    return target_line, qasm, last_qubit


def generate_ksat_expression(n, m, k):
    """
    Generate an arbitrary k-SAT expression according to the given parameters.

    Args:
        n: The number of groups
        m: The number of variables in a group
        k: The number of variables

    Returns: A Boolean expression
    """

    if m > k:
        raise ValueError("m > k not possible for kSAT")

    alphabet = []
    for i in range(k):
        alphabet.append(chr(97+i))

    expression = ""

    for i in range(n):
        literals = random.sample(alphabet, m)
        expression += " and ({}".format(literals[0])
        for l in literals[1:]:
            if random.random() < 0.5:
                expression += " or not({})".format(l)
            else:
                expression += " or {}".format(l)
        expression += ")"

    return expression.lstrip("and ")

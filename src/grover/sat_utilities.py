import boolean
from boolean.boolean import AND, OR, NOT, Symbol
import random


def generate_sat_oracle_reuse_gates(expr: boolean.Expression, control_names, is_toplevel=False):
    """
    Generate the circuit needed for an oracle solving the SAT problem, given a boolean expression.
    This uses a new ancillary qubit for every boolean gate, UNLESS that sub-expression has already been calculated before.

    Args:
        expr: The boolean expression (instance of boolean.Expression, not a string)
        control_names: The names of the control variables
        is_toplevel: Whether this is the main call, or a recursive call

    Returns: A tuple of the following values:
        - qasm: The QASM for this expression
        - target_qubit: The qubit line on which the output of this expression is placed
    """

    global highest_qubit_used
    global expressions_calculated

    if is_toplevel:
        highest_qubit_used = len(control_names)
        expressions_calculated = {}
    local_qasm = ""

    # go through possible types
    if type(expr) == AND or type(expr) == OR:
        # left side
        left_qasm, left_qubit, _ = generate_sat_oracle_reuse_gates(expr.args[0], control_names)
        expressions_calculated[expr.args[0]] = left_qubit
        right_qasm, right_qubit, _ = generate_sat_oracle_reuse_gates(expr.args[1], control_names)
        expressions_calculated[expr.args[1]] = right_qubit
        local_qasm += left_qasm
        local_qasm += right_qasm
    elif type(expr) == NOT:
        inner_qasm, inner_qubit, _ = generate_sat_oracle_reuse_gates(expr.args[0], control_names)
        local_qasm += inner_qasm
        local_qasm += "X q[{}]\n".format(inner_qubit)
        return local_qasm, inner_qubit, highest_qubit_used
    elif type(expr) == Symbol:
        # nothing to do here
        return local_qasm, control_names.index(expr), highest_qubit_used
    else:
        raise ValueError("Unknown boolean expr type: {}".format(type(expr)))

    if expr in expressions_calculated:
        already_calculated_index = expressions_calculated[expr]
        # we don't need to add any qasm, just say where this expression can be found
        return "", already_calculated_index, highest_qubit_used

    if is_toplevel:
        target_qubit = len(control_names)
        local_qasm += "H q[{}]\n".format(len(control_names))
        left_half_qasm = local_qasm[:]
    else:
        # we need another ancillary bit
        highest_qubit_used += 1
        target_qubit = highest_qubit_used

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

    # indicate to other calls of this function that this expression has been generated already
    expressions_calculated[expr] = target_qubit

    if is_toplevel:
        local_qasm += "\n".join(left_half_qasm.split("\n")[::-1])
        return local_qasm, target_qubit, highest_qubit_used

    return local_qasm, target_qubit, highest_qubit_used


def generate_sat_oracle_reuse_qubits(expr, control_names, avoid, last_qubit=-1, is_toplevel=False):
    """
    Generate a SAT oracle that saves on ancillary qubits by resetting them, so that they can be reused.

    Args:
        expr: The boolean expression to generate an oracle for
        avoid: The ancillary lines that we can't use because they already contain data (default is an empty list)
        control_names: The names of the variables in the expression (such as "a", "b" and "c")
        last_qubit: The highest qubit index we have ever used. This is needed to calculate the total number of ancillaries
        is_toplevel: Whether this function call is the "original". In that case, its output is a specific qubit line

    Returns: A tuple of the following values:
        - target_line: The output line of the qasm representing the input expression
                       All other lines are guaranteed to be reset to 0
        - qasm: The QASM code
        - last_qubit: The highest ancillary qubit index encountered in this expression
    """

    first_ancillary_bit = len(control_names) + 1

    if len(expr.args) > 2:
        raise ValueError("Fancy SAT Oracle expects only 1 and 2-argument expressions, but got {}".format(expr.args))

    if type(expr) == Symbol:
        return "", control_names.index(expr), last_qubit
    elif type(expr) == NOT:
        qubit_index = control_names.index(expr.args[0])
        return "X q[{}]".format(qubit_index), qubit_index, last_qubit
    elif type(expr) == AND:
        generate_func = generate_and
    elif type(expr) == OR:
        generate_func = generate_or
    else:
        raise ValueError("Unknown type in Boolean expression: {}".format(type(expr)))

    left_expr = expr.args[0]
    right_expr = expr.args[1]

    left_qasm, left_target_qubit, left_last_qubit = generate_sat_oracle_reuse_qubits(left_expr, control_names,
                                                                                     avoid[:],
                                                                                     last_qubit)
    avoid.append(left_target_qubit)
    right_qasm, right_target_qubit, right_last_qubit = generate_sat_oracle_reuse_qubits(right_expr, control_names,
                                                                                        avoid[:],
                                                                                        last_qubit)
    avoid.append(right_target_qubit)

    target_qubit = -1
    # if toplevel, we know what to target: the specific line that is set to the |1> state
    if is_toplevel:
        target_qubit = first_ancillary_bit - 1
        my_qasm = "H q[{}]\n".format(target_qubit) + \
                  generate_func(left_target_qubit, right_target_qubit, target_qubit) + \
                  "H q[{}]\n".format(target_qubit)
    else:
        # find the lowest line we can use
        # if necessary, we can target an entirely new line (if all the others are used)
        for i in range(first_ancillary_bit, first_ancillary_bit + max(avoid) + 1):
            if i not in avoid:
                target_qubit = i
                break
        my_qasm = generate_func(left_target_qubit, right_target_qubit, target_qubit)

    last_qubit = max(last_qubit, max(avoid), left_last_qubit, right_last_qubit, target_qubit)

    local_qasm = "\n".join([
        left_qasm,
        right_qasm,
        my_qasm,
        *right_qasm.split("\n")[::-1],
        *left_qasm.split("\n")[::-1]
    ])

    return local_qasm, target_qubit, last_qubit


def generate_and(qubit_1, qubit_2, target_qubit):
    """
    Generate an AND in qasm code (just a Toffoli).
    """
    if qubit_1 == qubit_2:
        return "CNOT q[{}],q[{}]\n".format(qubit_1, target_qubit)

    return "Toffoli q[{}],q[{}],q[{}]\n".format(qubit_1, qubit_2, target_qubit)


def generate_or(qubit_1, qubit_2, target_qubit):
    """
    Generate an OR in qasm code (Toffoli with X gates).
    """
    if qubit_1 == qubit_2:
        return "CNOT q[{}],q[{}]\n".format(qubit_1, target_qubit)

    local_qasm = "X q[{},{}]\n".format(qubit_1, qubit_2)
    local_qasm += generate_and(qubit_1, qubit_2, target_qubit)
    local_qasm += "X q[{},{},{}]\n".format(qubit_1, qubit_2, target_qubit)
    return local_qasm


def split_expression_evenly(expr):
    """
    Split a Boolean expression as evenly as possible into a binary tree.

    Args:
        expr: The Boolean expression to split

    Returns: The same expression, where all gates are applied to exactly 2 elements
    """

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

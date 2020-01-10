from settings import *
import matplotlib.pyplot as plt


def fill(character):
    """
    Apply a specific gate to all data qubits
    Args:
        character: The QASM gate to apply

    Returns: Valid QASM to append to the program
    """
    return "{} q[0:{}]\n".format(character, DATA_QUBITS - 1)


def n_size_cnot(n):
    """
    Generate a CNOT with n-1 control bits
    Args:
        n: The number of data bits

    Returns: Valid QASM to append to the program
    """
    if n == 2:
        local_qasm = "CNOT q[0],q[1]\n"
    elif n == 3:
        local_qasm = "Toffoli q[0],q[1],q[2]\n"
    elif n >= 4:
        gates_to_and = list(range(n - 1))
        control_count = 0
        gate_list = []
        while len(gates_to_and) > 0:
            a, b = gates_to_and[:2]
            if len(gates_to_and) == 2:
                c = n - 1
                gates_to_and = []
            else:
                c = n + control_count
                control_count += 1
                gates_to_and = gates_to_and[2:] + [c]
            gate_list.append("Toffoli q[{}],q[{}],q[{}]".format(a, b, c))

        gate_list = gate_list + gate_list[-2::-1]
        local_qasm = "\n".join(gate_list) + "\n"
    else:
        raise ValueError("Toffoli size not supported: {}".format(n))

    return local_qasm


def toffoli_penis():
    """
    Generate a common structure that applies a Hadamard, CNOT, and Hadamard again to the lowest data bit

    Returns: Valid QASM to append to the program
    """
    local_qasm = "H q[{}]\n".format(DATA_QUBITS - 1)
    local_qasm += n_size_cnot(DATA_QUBITS)
    local_qasm += "H q[{}]\n".format(DATA_QUBITS - 1)
    return local_qasm


def oracle():
    """
    Generate a common structure that is used in the oracle circuit.
    It flips all bits that correspond to a 0 in the search target.

    Returns: Valid QASM to append to the program
    """
    local_qasm = "X q["
    for i in range(DATA_QUBITS):
        if SEARCH_TARGET[i] == "0":
            local_qasm += str(i) + ","

    # remove last comma and add closing bracket
    local_qasm = local_qasm[:-1] + "]\n"
    return local_qasm


def int_to_bits(int_str):
    """
    Convert a number (possibly in string form) to a readable bit format.
    For example, the result '11', which means both qubits were measured as 1, is returned by the API as "3".
    This converts that output to the readable version.

    Args:
        int_str: A string or integer in base 10 that represents the measurement outcome.

    Returns: A string of 0's and 1's
    """
    return str(bin(int(int_str)))[2:].zfill(QUBIT_COUNT)


def interpret_results(result_dict, plot=True):
    """
    Parse the result dictionary given by the API into a readable format, and plot it.

    Args:
        result_dict: The dictionary given by qi.execute_qasm
        plot: Whether to plot the results in a bar chart

    Returns: Parsed result
    """
    num_of_measurements = 2 ** QUBIT_COUNT
    ordered_bars = [None for _ in range(num_of_measurements)]

    for i in range(num_of_measurements):
        # find result in dictionary and add to list of bars
        try:
            bar = result_dict["histogram"][str(i)]
        except KeyError:
            bar = 0

        # generate corresponding binary name (so "11" instead of "3")
        name = int_to_bits(i)

        ordered_bars[i] = (name, bar)

    if plot:
        for b in ordered_bars:
            plt.bar(*b)
        plt.title("Measurements, q[0] is the last bit")
        plt.show()

    return ordered_bars
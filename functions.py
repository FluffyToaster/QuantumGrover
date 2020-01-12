from settings import *
import matplotlib.pyplot as plt


def fill(character):
    """
    Apply a specific gate to all data qubits
    Args:
        character: The QASM gate to apply

    Returns: Valid QASM to append to the program
    """
    # create a list of the qubit indices that need the gate applied
    indices = ",".join(map(str, range(DATA_QUBITS)))

    return "{} q[{}]\n".format(character, indices)


def n_size_cnot(n):
    """
    Generate a CNOT with n control bits.
    It is assumed the control bits have indices [0:n-1],
    and the target bit is at index [n].

    Args:
        n: The number of control bits

    Returns: Valid QASM to append to the program
    """

    if n == 1:
        local_qasm = "CNOT q[0],q[1]\n"
    elif n == 2:
        local_qasm = "Toffoli q[0],q[1],q[2]\n"
    else:
        # for n > 2, there is no direct instruction in QASM, so we must generate an equivalent circuit
        # the core idea of a large CNOT is that we must AND-gate together all the control bits
        # we do this with Toffoli gates, and store the result of each Toffoli on ancillary qubits

        # we keep a list of all the bits that should be AND-ed together
        bits_to_and = list(range(n))
        ancillary_count = 0

        # make a list of all the Toffoli gates to eventually write to the program
        gate_list = []

        # we will continue looping until all bits are and-ed together
        while len(bits_to_and) > 0:
            # take the first two
            a, b = bits_to_and[:2]
            # if these are the only two elements to AND, we're almost done!
            # just combine these 2 in a Toffoli...
            # ...which targets the global "target bit" of this n-CNOT
            if len(bits_to_and) == 2:
                target = n
                bits_to_and = []

            # the default case is to write the result to an ancillary bit
            else:
                target = n + 1 + ancillary_count
                ancillary_count += 1
                # remove the used qubits from the list of bits to AND
                bits_to_and = bits_to_and[2:] + [target]

            gate_list.append("Toffoli q[{}],q[{}],q[{}]".format(a, b, target))

        # Apply the complete list of gates in reverse after the target is flipped
        # This undoes all operations on the ancillary bits (so they remain 0)
        gate_list = gate_list + gate_list[-2::-1]
        local_qasm = "\n".join(gate_list) + "\n"

    return local_qasm


def cnot_pillar():
    """
    Generate a common structure that applies a Hadamard, CNOT, and Hadamard again to the lowest data bit

    Returns: Valid QASM to append to the program
    """
    local_qasm = "H q[{}]\n".format(DATA_QUBITS - 1)
    local_qasm += n_size_cnot(DATA_QUBITS - 1)
    local_qasm += "H q[{}]\n".format(DATA_QUBITS - 1)
    return local_qasm


def oracle(search_term):
    """
    Generate a common structure that is used in the oracle circuit.
    It flips all bits that correspond to a 0 in the search target.

    Returns: Valid QASM to append to the program
    """
    if "0" not in search_term:
        return "\n"

    local_qasm = "X q["
    for i in range(DATA_QUBITS):
        if search_term[i] == "0":
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
    # convert to an integer, then generate the binary string
    # remove the "0b" prefix from the binary string
    # then pad (using zfill) with 0's
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

    # we still store the histogram bars in here, and later sort them in ascending order
    ordered_bars = [None for _ in range(num_of_measurements)]

    for i in range(num_of_measurements):
        # find result in dictionary and add to list of bars
        # zero-valued bars don't show up in the dictionary, hence the try-except
        try:
            bar = result_dict["histogram"][str(i)]
        except KeyError:
            bar = 0

        # generate corresponding binary name (so "11" instead of "3")
        name = int_to_bits(i)

        ordered_bars[i] = (hex(int(name, 2))[2:], bar)

    if plot:
        for b in ordered_bars:
            # check if the given bar has 0's for all the ancillary bits
            # if it does not, we assume it is irrelevant for the histogram, so we don't plot it
            if int(b[0], 16) < 2**DATA_QUBITS:
                plt.bar(b[0], b[1])
            # if a result is returned where some ancillary bits were not zero, we have a problem
            elif b[1] != 0:
                raise ValueError("\tNonzero result from 'impossible' measurement:\n"
                                 "\tColumn {} has fraction {}. This means not all control bits were 0!".format(b[0],
                                                                                                               b[1]))

        # set styling for the x-axis markers
        plt.xticks(fontsize=6, rotation=45, ha="right")
        plt.title("Measurements, q[0] is the last bit, ancillary qubits omitted")
        plt.show()

    return ordered_bars

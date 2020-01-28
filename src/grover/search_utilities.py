import matplotlib.pyplot as plt
import math


def apply(gate, qubit):
    """
    Simply apply a gate to a single qubit

    Args:
        gate: The gate to apply
        qubit: The target qubit

    Returns: Valid QASM that represents this application

    """
    return "{} q[{}]\n".format(gate, qubit)


def fill(character, data_qubits):
    """
    Apply a specific gate to all data qubits
    Args:
        character: The QASM gate to apply
        data_qubits: The number of data qubits

    Returns: Valid QASM to append to the program
    """
    # create a list of the qubit indices that need the gate applied
    indices = ",".join(map(str, range(data_qubits)))

    return "{} q[{}]\n".format(character, indices)


def normal_n_size_cnot(n, mode):
    """
    Generate a CNOT with n control bits.
    It is assumed the control bits have indices [0:n-1],
    and the target bit is at index [n].

    Args:
        n: The number of control bits
        mode: The method by which we will make CNOT gates

    Returns: Valid QASM to append to the program
    """

    if n == 1:
        local_qasm = "CNOT q[0],q[1]\n"
    elif n == 2:
        # if mode == "no toffoli":
        #     local_qasm = alternative_toffoli(0, 1, 2)
        # else:
        #     local_qasm = "Toffoli q[0],q[1],q[2]\n"
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

            # if mode == "no toffoli":
            #     gate_list.append(alternative_toffoli(a, b, target))
            # else:
            #     gate_list.append("Toffoli q[{}],q[{}],q[{}]".format(a, b, target))
            gate_list.append("Toffoli q[{}],q[{}],q[{}]".format(a, b, target))

        # Apply the complete list of gates in reverse after the target is flipped
        # This undoes all operations on the ancillary qubits (so they remain 0)
        gate_list = gate_list + gate_list[-2::-1]
        local_qasm = "\n".join(gate_list) + "\n"

    return local_qasm


def n_size_crot(n, start_n, target, angle):
    """
    Generate a controlled rotation with n control bits without using Toffoli gates.
    It is assumed the control bits have indices [start_n : start_n + n-1].

    Args:
        n: The number of control bits
        start_n: The first index that is a control bit
        target: The target bit index
        angle: The angle in radians by which to shift the phase
               An angle of pi gives an H-Z-H aka X gate
               An angle of pi/2 gives an H-S-H gate
               An angle of pi/4 gives an H-T-H gate
               Etc.

    Returns: Valid QASM to append to the program
    """
    local_qasm = ""

    if n == 1:
        # Simply a CROT with the given angle
        local_qasm += apply("H", target)
        local_qasm += "CR q[{}],q[{}],{}\n".format(start_n, target, angle)
        local_qasm += apply("H", target)
    else:
        # V gate using the lowest control bit
        local_qasm += n_size_crot(1, start_n + n - 1, target, angle / 2)

        # n-1 CNOT on highest bits (new_angle = angle)
        local_qasm += n_size_crot(n - 1, 0, start_n + n - 1, math.pi)

        # V dagger gate on lowest two bits
        local_qasm += n_size_crot(1, start_n + n - 1, target, -angle / 2)

        # n-1 CNOT on highest bits (new_angle = angle)
        local_qasm += n_size_crot(n - 1, 0, start_n + n - 1, math.pi)

        # controlled V gate using highest as controls and lowest as target (new_angle = angle / 2)
        local_qasm += n_size_crot(n - 1, 0, target, angle / 2)

    return local_qasm


def alternative_toffoli(control_1, control_2, target):
    """
    Generate a circuit from 1 and 2 qubit gates that performs an operation equivalent to a Toffoli gate.

    Args:
        control_1: First control bit index
        control_2: Second control bit index
        target: Target bit index

    Returns: Valid QASM that performs a CCNOT
    """

    local_qasm = ""
    local_qasm += apply("H", target)
    local_qasm += "CR q[{}],q[{}],{}\n".format(control_2, target, math.pi / 2)
    # local_qasm += apply("H", target)

    local_qasm += "CNOT q[{}],q[{}]\n".format(control_1, control_2)

    # local_qasm += apply("H", target)
    local_qasm += "CR q[{}],q[{}],{}\n".format(control_2, target, -math.pi / 2)
    # local_qasm += apply("H", target)

    local_qasm += "CNOT q[{}],q[{}]\n".format(control_1, control_2)

    # local_qasm += apply("H", target)
    local_qasm += "CR q[{}],q[{}],{}\n".format(control_1, target, math.pi / 2)
    local_qasm += apply("H", target)

    return local_qasm


def cnot_pillar(mode, data_qubits):
    """
    Generate a common structure that applies a Hadamard, CNOT, and Hadamard again to the lowest data bit

    Returns: Valid QASM to append to the program
    """
    local_qasm = "H q[{}]\n".format(data_qubits - 1)
    if mode in ["normal", "no toffoli"]:
        local_qasm += normal_n_size_cnot(data_qubits - 1, mode)
    elif mode == "crot":
        local_qasm += n_size_crot(data_qubits - 1, 0, data_qubits - 1, math.pi)
    elif mode == "fancy cnot":
        local_qasm += fancy_cnot(data_qubits - 1)
    local_qasm += "H q[{}]\n".format(data_qubits - 1)
    return local_qasm


def search_oracle(search_term, data_qubits):
    """
    Generate a common structure that is used in the oracle circuit.
    It flips all bits that correspond to a 0 in the search target.
    Args:
        search_term: The search term for which to generate an oracle
        data_qubits: The number of data qubits

    Returns: Valid QASM to append to the program
    """
    if "0" not in search_term:
        return "\n"

    local_qasm = "X q["
    for i in range(data_qubits):
        if search_term[i] == "0":
            local_qasm += str(i) + ","

    # remove last comma and add closing bracket
    local_qasm = local_qasm[:-1] + "]\n"
    return local_qasm


def int_to_bits(int_str, qubit_count):
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
    return str(bin(int(int_str)))[2:].zfill(qubit_count)


def interpret_results(result_dict, qubit_count, data_qubits, plot=True):
    """
    Parse the result dictionary given by the API into a readable format, and plot it.

    Args:
        result_dict: The dictionary given by qi.execute_qasm
        plot: Whether to plot the results in a bar chart

    Returns: Parsed result
    """

    num_of_measurements = 2 ** qubit_count

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
        name = int_to_bits(i, qubit_count)

        ordered_bars[i] = (name, bar)

    if plot:
        for b in ordered_bars:
            # check if the given bar has 0's for all the ancillary qubits
            # if it does not, we assume it is irrelevant for the histogram, so we don't plot it
            if int(b[0], 2) < 2 ** data_qubits:
                plt.bar(b[0][-data_qubits:], b[1])
            # if a result is returned where some ancillary qubits were not zero, we have a problem
            elif b[1] != 0:
                raise ValueError("\tNonzero result from 'impossible' measurement:\n"
                                 "\tColumn {} has fraction {}. This means not all control bits were 0!".format(b[0],
                                                                                                               b[1]))

        # set styling for the x-axis markers
        plt.xticks(fontsize=6, rotation=45, ha="right")
        plt.title("Measurements, q[0] is the last bit, ancillary qubits omitted")
        plt.show()

    return ordered_bars


def gray_code(n):
    """
    Generate a Gray code sequence of bit string with length n.

    Args:
        n: The size for each element in the Gray code

    Returns: An array of strings forming a Gray code
    """

    if n == 1:
        return ["0", "1"]
    else:
        g_previous = gray_code(n - 1)
        mirrored_paste = g_previous + g_previous[::-1]
        g_current = mirrored_paste[:]
        for i in range(2**n):
            if i < 2**(n-1):
                g_current[i] = g_current[i] + "0"
            else:
                g_current[i] = g_current[i] + "1"
        return g_current


def fancy_cnot(n):
    """
    Generate a circuit equivalent to an n-bit CNOT.
    This avoids using Toffoli gates or ancillary qubits.
    Args:
        n: Number of control bits

    Returns: Valid QASM that represents a CNOT

    """
    gray_code_list = gray_code(n)[1:]
    local_qasm = apply("H", n)

    for i in range(len(gray_code_list)):
        if i == 0:
            local_qasm += "CR q[0],q[{}],{}\n".format(n, math.pi/(2**(n-1)))
        else:
            prev_gray = gray_code_list[i-1]
            cur_gray = gray_code_list[i]

            flip_idx = -1
            for j in range(len(cur_gray)):
                if cur_gray[j] != prev_gray[j]:
                    flip_idx = j
                    break

            last_1_bit_cur = len(cur_gray) - 1 - cur_gray[::-1].index("1")
            last_1_bit_prev = len(prev_gray) - 1 - prev_gray[::-1].index("1")

            bit_a = flip_idx

            if flip_idx == last_1_bit_cur:
                bit_b = last_1_bit_prev
            else:
                bit_b = last_1_bit_cur

            control_bit = min(bit_a, bit_b)
            target_bit = max(bit_a, bit_b)

            local_qasm += "CNOT q[{}],q[{}]\n".format(control_bit, target_bit)

            parity = cur_gray.count("1") % 2
            if parity == 0:
                angle = -math.pi/(2**(n-1))
            else:
                angle = math.pi/(2**(n-1))

            local_qasm += "CR q[{}],q[{}],{}\n".format(target_bit, n, angle)

    local_qasm += apply("H", n)
    return local_qasm

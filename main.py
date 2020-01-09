from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI
import matplotlib.pyplot as plt
import math

DATA_QUBITS = 6
CONTROL_QUBITS = int(math.floor(DATA_QUBITS / 2))
QUBIT_COUNT = DATA_QUBITS + CONTROL_QUBITS
SEARCH_TARGET = "111011"[::-1]
SHOT_COUNT = 512


def fill(character):
    local_qasm = ""
    for i in range(DATA_QUBITS):
        local_qasm += "{} q[{}]\n".format(character, i)
    return local_qasm


def n_size_cnot(n):
    if n == 2:
        local_qasm = "CNOT q[0],q[1]\n"
    elif n == 3:
        local_qasm = "Toffoli q[0],q[1],q[2]\n"
    elif n == 4:
        local_qasm = """
        Toffoli q[0],q[1],q[4]
        Toffoli q[2],q[4],q[3]
        Toffoli q[0],q[1],q[4]
        """
    elif n == 5:
        local_qasm = """
        Toffoli q[0], q[1], q[5]
        Toffoli q[2], q[3], q[6]
        Toffoli q[5], q[6], q[4]
        Toffoli q[2], q[3], q[6]
        Toffoli q[0], q[1], q[5]
        """
    elif n == 6:
        local_qasm = """
        Toffoli q[0], q[1], q[6]
        Toffoli q[2], q[3], q[7]
        Toffoli q[4], q[6], q[8]
        Toffoli q[7], q[8], q[5]
        Toffoli q[4], q[6], q[8]
        Toffoli q[2], q[3], q[7]
        Toffoli q[0], q[1], q[6]
        """
    else:
        raise ValueError("Toffoli size not supported: {}".format(n))

    return local_qasm


def toffoli_penis():
    local_qasm = "H q[{}]\n".format(DATA_QUBITS - 1)
    local_qasm += n_size_cnot(DATA_QUBITS)
    local_qasm += "H q[{}]\n".format(DATA_QUBITS - 1)
    return local_qasm


def oracle():
    local_qasm = ""
    for i in range(DATA_QUBITS):
        if SEARCH_TARGET[i] == "0":
            local_qasm += "X q[{}]\n".format(i)
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


def interpret_results(result_dict):
    """
    Parse the result dictionary given by the API into a readable format, and plot it.

    Args:
        result_dict: The dictionary given by qi.execute_qasm

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

        # reverse order of name bits, because QAPI
        ordered_bars[i] = (name, bar)

    for b in ordered_bars:
        plt.bar(*b)
    plt.title("Measurements, q[0] is the last bit")
    plt.show()
    return ordered_bars


enable_account("58957ea5a48a801eb5af6adcae7776126c122c9d")
qi = QuantumInspireAPI()

print("Logged in to QI account")

qasm = """

version 1.0

qubits {}

""".format(QUBIT_COUNT)

# initialisation
qasm += fill("H")

# looping grover
for iteration in range(int(math.pi * math.sqrt(2 ** DATA_QUBITS) / 4)):

    # oracle
    qasm += oracle()
    qasm += toffoli_penis()
    qasm += oracle()

    # diffusion
    qasm += fill("H")
    qasm += fill("X")
    qasm += toffoli_penis()
    qasm += fill("X")
    qasm += fill("H")

backend = qi.get_backend_type_by_name('QX single-node simulator')

print("Executing QASM code ({} qubits, {} shots)".format(QUBIT_COUNT, SHOT_COUNT))
result = qi.execute_qasm(qasm, backend_type=backend, number_of_shots=SHOT_COUNT)
print("Execution complete, printing and plotting results")
histogram_list = interpret_results(result)
for h in histogram_list:
    if h[0] == SEARCH_TARGET[::-1].zfill(QUBIT_COUNT):
        print("Probability of search target: {}".format(h[1]))


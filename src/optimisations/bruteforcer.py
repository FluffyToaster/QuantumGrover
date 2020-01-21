import numpy as np
import itertools

i = np.matrix([[1,0],
               [0,1]])

x = np.matrix([[0,1],
               [1,0]])

y = np.matrix([[0,-1j],
               [1j,0]])

z = np.matrix([[1,0],
               [0,-1]])

h = np.matrix([[1,1],
               [1,-1]])

toffoli = np.matrix([[1,0,0,0,0,0,0,0],
                     [0,1,0,0,0,0,0,0],
                     [0,0,1,0,0,0,0,0],
                     [0,0,0,1,0,0,0,0],
                     [0,0,0,0,1,0,0,0],
                     [0,0,0,0,0,1,0,0],
                     [0,0,0,0,0,0,0,1],
                     [0,0,0,0,0,0,1,0]])

GATE_SET = {"X": x,
            "Y": y,
            "Z": z,
            "I": i,
            "H": h}


def double_tensor(a,b):
    return np.tensordot(a, b, axes=0).transpose((0, 2, 1, 3)).reshape((4, 4))


def triple_tensor(a,b,c):
    return np.tensordot(a, np.tensordot(b, c, axes=0).transpose((0, 2, 1, 3)).reshape((4, 4)), axes=0).transpose((0, 2, 1, 3)).reshape((8, 8))


def normalize(m):
    nonzero_elem = m[0,0]
    if nonzero_elem == 0:
        nonzero_elem = m[0,1]
    return m / nonzero_elem


def multi(*args):
    if len(args) == 1:
        return args[0]

    last_two = np.matmul(args[-2], args[-1])
    if len(args) == 2:
        return last_two

    return multi(*args[:-2], last_two)


def find_equivalent_to(*gates):
    unitary = normalize(multi(*gates))

    matches = []

    REPL_GATE_SET = {"X": x,
                     "Y": y,
                     "Z": z,
                     "H": h}

    max_len = 3
    for l in range(2, max_len + 1):
        for prod in itertools.product(REPL_GATE_SET.keys(), repeat=l):
            matrices = list(map(lambda x: REPL_GATE_SET[x], prod))
            matrix = normalize(multi(*matrices))
            if (unitary == matrix).all():
                matches.append("".join(prod))
                print("MATCH: {}".format(prod))
    return matches


def generate_optimisation_dict():
    optimisation_dict = {}

    for gate in ["H", "X", "Y", "I", "Z"]:
        for match in find_equivalent_to(GATE_SET[gate]):
            optimisation_dict[match] = gate.replace("I", "")

    return optimisation_dict

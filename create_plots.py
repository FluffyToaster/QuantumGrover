from src.grover.run_grover import *
import matplotlib.pyplot as plt

# 4 IMPLEMENTATION GROVER SEARCH LINE COUNT PLOT
x_values = []
opt_norm_values = []
unopt_norm_values = []
opt_fancy_values = []
unopt_fancy_values = []

for i in range(3, 12):
    x_values.append(i)

    opt_norm = grover_search_qasm(["1" * i], "no toffoli")[1]
    opt_norm_values.append(opt_norm)

    unopt_norm = grover_search_qasm(["1" * i], "no toffoli", apply_optimisation=False)[1]
    unopt_norm_values.append(unopt_norm)

    opt_fancy = grover_search_qasm(["1" * i], "fancy cnot")[1]
    opt_fancy_values.append(opt_fancy)

    unopt_fancy = grover_search_qasm(["1" * i], "fancy cnot", apply_optimisation=False)[1]
    unopt_fancy_values.append(unopt_fancy)

plt.title("Scaling of different CNOT implementations")
plt.yscale("log")
plt.xlabel("Length of search string")
plt.ylabel("Number of quantum operations (approximate)")
plt.plot(x_values, unopt_norm_values, c="orange", ls="-", label="Using n-3 ancillary bits")
plt.plot(x_values, opt_norm_values, c="blue", ls="-", label="Using n-3 ancillary bits (optimised)")
plt.plot(x_values, unopt_fancy_values, c="red", ls="-", label="Using no ancillary bits")
plt.plot(x_values, opt_fancy_values, c="green", ls="-", label="Using no ancillary bits (optimised)")
plt.legend()

plt.show()


# SAT VS CLASSICAL PLOT
bool_expression = "(a and b)"
x_values = []
sat_values = []
classical_values = []
qubit_counts = []

for i in range(3, 12):
    x_values.append(i)

    bool_expression = "(" + bool_expression + " and {})".format(chr(96+i))
    _, sat_val, qubit_count, _ = grover_sat_qasm(bool_expression, "no toffoli")

    sat_values.append(sat_val)
    qubit_counts.append(qubit_count)
    classical_values.append((2 ** i) * i)

fig, ax1 = plt.subplots()

plt.title("Scaling of classical vs quantum SAT solving")
plt.yscale("log")
ax1.set_xlabel("Number of boolean variables")
ax1.set_ylabel("Number of operations (approximate)")
ax1.plot(x_values, sat_values, c="blue", ls="-", label="SAT Solver using Grover (optimised)")
ax1.plot(x_values, classical_values, c="red", ls="-", label="Classical (exhaustive) SAT Solver")

ax2 = ax1.twinx()
ax2.plot(x_values, qubit_counts, c="green", ls="--", label="Number of qubits required for Grover")

ax1.legend()
ax2.legend(loc="lower right")

plt.show()


# NAIVE VS SMART MULTI-ELEMENT SEARCH
searchables = [
    "10101010",
    "01010110",
    "10011010",
    "11010010",
    "10010110",
    "11001010",
    "11000110"
]

x_values = []
naive_values = []
smart_values = []

for i in range(1, len(searchables)):
    x_values.append(i)
    to_search = searchables[:i]
    naive_count = 0
    for t in to_search:
        naive_count += grover_search_qasm([t], "no toffoli")[1]
    naive_values.append(naive_count)

    multi_count = grover_search_qasm(to_search, "no toffoli")[1]
    smart_values.append(multi_count)

plt.title("Naive vs optimal multi-element search")
plt.xlabel("Number of search elements")
plt.ylabel("Number of quantum operations (approximate)")
plt.plot(x_values, naive_values, c="orange", ls="-", label="Naive multi-element search")
plt.plot(x_values, smart_values, c="blue", ls="-", label="Optimal multi-element search")
plt.legend()

plt.show()

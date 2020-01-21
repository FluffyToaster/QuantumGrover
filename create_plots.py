from src.grover.run_grover import *
import matplotlib.pyplot as plt
import numpy as np

FONTSIZE_AXES = 13
FONTSIZE_LEGEND = 13

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

    unopt_norm = grover_search_qasm(["1" * i], "no toffoli", apply_optimization=False)[1]
    unopt_norm_values.append(unopt_norm)

    opt_fancy = grover_search_qasm(["1" * i], "fancy cnot")[1]
    opt_fancy_values.append(opt_fancy)

    unopt_fancy = grover_search_qasm(["1" * i], "fancy cnot", apply_optimization=False)[1]
    unopt_fancy_values.append(unopt_fancy)

# plt.title("Scaling of different CNOT implementations")
plt.yscale("log")
plt.xlabel("Length of search string", fontsize=FONTSIZE_AXES)
plt.ylabel("Number of quantum operations", fontsize=FONTSIZE_AXES)
plt.plot(x_values, unopt_fancy_values, c="red", ls="-", label="No ancillary bits")
plt.plot(x_values, opt_fancy_values, c="green", ls="-", label="No ancillary bits (optimized)")
plt.plot(x_values, unopt_norm_values, c="orange", ls="-", label="N-3 ancillary bits")
plt.plot(x_values, opt_norm_values, c="blue", ls="-", label="N-3 ancillary bits (optimized)")
plt.legend(fontsize=FONTSIZE_LEGEND)

plt.savefig("plots/4_impl.png")
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

# plt.title("Scaling of classical vs quantum SAT solving")
plt.yscale("log")
ax1.set_xlabel("Number of boolean variables", fontsize=FONTSIZE_AXES)
ax1.set_ylabel("Number of operations", fontsize=FONTSIZE_AXES)
ax1.plot(x_values, classical_values, c="red", ls="-", label="Classical (exhaustive) SAT Solver")
ax1.plot(x_values, sat_values, c="blue", ls="-", label="SAT Solver using Grover (optimized)")

# ax2 = ax1.twinx()
# ax2.plot(x_values, qubit_counts, c="green", ls="--", label="Number of qubits required for Grover")

ax1.legend(fontsize=FONTSIZE_LEGEND)
# ax2.legend(loc="lower right")
plt.savefig("plots/sat_scaling.png")
plt.show()


# NAIVE VS SMART MULTI-ELEMENT SEARCH
searchables = [
    "00000001" + 3 * "1",
    "00000010" + 3 * "1",
    "00000100" + 3 * "1",
    "00001000" + 3 * "1",
    "00010000" + 3 * "1",
    "00100000" + 3 * "1",
    "01000000" + 3 * "1",
    "10000000" + 3 * "1",
    "10000001" + 3 * "1",
    "10000010" + 3 * "1",
    "10000100" + 3 * "1",
    "10001000" + 3 * "1",
    "10010000" + 3 * "1",
    "10100000" + 3 * "1",
    "11000000" + 3 * "1"
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

# plt.title("Naive vs optimal multi-element search")
plt.xlabel("Number of search elements", fontsize=FONTSIZE_AXES)
plt.ylabel("Number of quantum operations", fontsize=FONTSIZE_AXES)
plt.plot(x_values, naive_values, c="orange", ls="-", label="Naive multi-element search")
plt.plot(x_values, smart_values, c="blue", ls="-", label="Optimal multi-element search")
plt.legend(fontsize=FONTSIZE_LEGEND)

plt.savefig("plots/naive_opt_mult_search.png")
plt.show()


# MIN-AVG-MAX RUNTIME PLOT
read_file = open("results\plot_data 1579173336.txt", "r")
lines = read_file.read(-1).split("\n")

result_lists = {}

for i in lines:
    if i == "": continue
    qubits, runtime, _, _ = i.split(", ")
    qubits = int(qubits)
    runtime = float(runtime)
    if qubits in result_lists:
        result_lists[qubits].append(runtime)
    else:
        result_lists[qubits] = [runtime]

x_values = []
filtered_avgs = []
stds = []
mins = []
maxs = []

for qubits, runtimes in result_lists.items():
    avg = sum(runtimes) / len(runtimes)
    std = np.std(runtimes)

    filtered_runtimes = list(filter(lambda value: value < avg + std, runtimes))
    print(avg, std)
    print(runtimes)
    print(filtered_runtimes)
    print()
    filtered_avg = sum(filtered_runtimes) / len(filtered_runtimes)

    x_values.append(qubits)
    filtered_avgs.append(filtered_avg)
    mins.append(min(runtimes))
    maxs.append(max(runtimes))
    stds.append(np.std(filtered_runtimes))

plt.yscale("log")
plt.plot(x_values, maxs, "r-", label="Maximum runtime")
plt.plot(x_values, filtered_avgs, "b-", label="Average runtime")
plt.plot(x_values, mins, "g-", label="Minimum runtime")
plt.legend(fontsize=FONTSIZE_LEGEND)

# plt.title("Speed of quantum simulation of Grover's search")
plt.xlabel("Length of search string", fontsize=FONTSIZE_AXES)
plt.ylabel("Runtime in seconds", fontsize=FONTSIZE_AXES)

plt.savefig("plots/min_avg_max_runtime.png")
plt.show()

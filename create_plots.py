from src.grover.run_grover import *
import matplotlib.pyplot as plt
import numpy as np

FONTSIZE_AXES = 13
FONTSIZE_LEGEND = 13

# shots to use in averaging
# every plot takes about 2*SHOT_COUNT seconds to generate
SHOT_COUNT = 15

# 4 IMPLEMENTATION GROVER SEARCH LINE COUNT PLOT
xrange = range(3, 12)
x_values = []
opt_norm_values = []
unopt_norm_values = []
opt_fancy_values = []
unopt_fancy_values = []

for i in xrange:
    opt_norm_values.append(0)
    unopt_norm_values.append(0)
    opt_fancy_values.append(0)
    unopt_fancy_values.append(0)

for i in xrange:
    x_values.append(i)

    for j in range(SHOT_COUNT):
        search_term = ["".join([random.choice("01") for _ in range(i)])]
        opt_norm = generate_search_qasm(search_term, "no toffoli")[1]
        opt_norm_values[i-3] = opt_norm / SHOT_COUNT

        unopt_norm = generate_search_qasm(search_term, "no toffoli", apply_optimization=False)[1]
        unopt_norm_values[i-3] = unopt_norm / SHOT_COUNT

        opt_fancy = generate_search_qasm(search_term, "fancy cnot")[1]
        opt_fancy_values[i-3] = opt_fancy / SHOT_COUNT

        unopt_fancy = generate_search_qasm(search_term, "fancy cnot", apply_optimization=False)[1]
        unopt_fancy_values[i-3] = unopt_fancy / SHOT_COUNT

# plt.title("Scaling of different CNOT implementations")
plt.yscale("log")
plt.xlabel("Length of search string", fontsize=FONTSIZE_AXES)
plt.ylabel("Number of quantum operations", fontsize=FONTSIZE_AXES)
plt.plot(x_values, unopt_fancy_values, c="red", ls="-", label="No ancillary qubits")
plt.plot(x_values, opt_fancy_values, c="green", ls="-", label="No ancillary qubits (optimized)")
plt.plot(x_values, unopt_norm_values, c="orange", ls="-", label=r"$n-3$ ancillary qubits")
plt.plot(x_values, opt_norm_values, c="blue", ls="-", label=r"$n-3$ ancillary qubits (optimized)")
plt.legend(fontsize=FONTSIZE_LEGEND, loc="upper left")
plt.grid()

plt.savefig("plots/4_impl.png")
plt.show()


# SAT VS CLASSICAL PLOT

xrange = list(range(2, 17))
SHOT_COUNT = 10

x_values = []
sat_values_normal = []
sat_values_fancy = []
classical_values_exhaustive = []
classical_values_decent = []

qubit_counts_normal = []
qubit_counts_fancy = []

for i in xrange:
    sat_values_normal.append(0)
    sat_values_fancy.append(0)
    classical_values_decent.append(0)
    classical_values_exhaustive.append(0)
    qubit_counts_normal.append(0)
    qubit_counts_fancy.append(0)

for i in xrange:
    x_values.append(i)

    group_count = 4
    group_size = i
    alphabet_size = i

    for j in range(SHOT_COUNT):
        bool_expression = generate_ksat_expression(group_count, group_size, alphabet_size)
        _, sat_val_normal, qubit_count_normal, _ = generate_sat_qasm(bool_expression, "normal", sat_mode="normal")
        _, sat_val_fancy, qubit_count_fancy, _ = generate_sat_qasm(bool_expression, "normal", sat_mode="fancy")

        sat_values_normal[i-2] += sat_val_normal / SHOT_COUNT
        sat_values_fancy[i-2] += sat_val_fancy / SHOT_COUNT
        qubit_counts_normal[i-2] += qubit_count_normal / SHOT_COUNT
        qubit_counts_fancy[i-2] += qubit_count_fancy / SHOT_COUNT

        operation_count = bool_expression.count("or") + bool_expression.count("not") + bool_expression.count("and")
        classical_values_exhaustive[i-2] += (2 ** alphabet_size) * operation_count / SHOT_COUNT
        classical_values_decent[i-2] += (2 * (1 - 1/group_size)) ** alphabet_size * 5 / SHOT_COUNT

fig, (ax1, ax2) = plt.subplots(nrows=2, gridspec_kw={'height_ratios': [2, 1]})
fig.set_figheight(7)

# plt.title("Scaling of classical vs quantum SAT solving")
ax1.set_yscale("log")
ax1.set_xlabel("Clause size (k) for k-SAT problem", fontsize=FONTSIZE_AXES)
ax1.set_ylabel("Number of operations", fontsize=FONTSIZE_AXES)
ax1.plot(x_values, sat_values_fancy, c="orange", ls="-", label="Grover (reuse ancillary qubits)")
ax1.plot(x_values, sat_values_normal, c="blue", ls="-", label="Grover (reuse gate results)")
ax1.plot(x_values, classical_values_exhaustive, c="red", ls="-", label="Classical (exhaustive)")
ax1.plot(x_values, classical_values_decent, c="purple", ls="-", label="Classical (optimal)")
ax1.grid()

ax2.set_yscale("linear")
ax2.set_xlabel("Clause size (k) for k-SAT problem", fontsize=FONTSIZE_AXES)
ax2.set_ylabel("Number of qubits", fontsize=FONTSIZE_AXES)
ax2.plot(x_values, qubit_counts_normal, c="blue", ls="--", label="Grover (reuse gate results)")
ax2.plot(x_values, qubit_counts_fancy, c="orange", ls="--", label="Grover (reuse ancillary qubits)")
ax2.grid()

ax1.legend(fontsize=FONTSIZE_LEGEND, loc="upper left")
ax2.legend(fontsize=FONTSIZE_LEGEND, loc="upper left")
plt.savefig("plots/sat_scaling.png")
plt.show()


# NAIVE VS SMART MULTI-ELEMENT SEARCH

SHOT_COUNT = 10
x_size = 10

x_values = []
avg_naive_values = []
avg_smart_values = []

for i in range(1, x_size + 1):
    x_values.append(i)
    avg_naive_values.append(0)
    avg_smart_values.append(0)

for j in range(SHOT_COUNT):
    searchables = [
        "".join([random.choice("01") for i in range(10)])
        for _ in range(x_size+1)
    ]

    naive_values = []
    smart_values = []

    for i in range(1, len(searchables)):
        to_search = searchables[:i]
        naive_count = 0
        for t in to_search:
            naive_count += generate_search_qasm([t], "no toffoli")[1]
        avg_naive_values[i-1] += naive_count / SHOT_COUNT

        multi_count = generate_search_qasm(to_search, "no toffoli")[1]
        avg_smart_values[i-1] += multi_count / SHOT_COUNT


# plt.title("Naive vs optimal multi-element search")
plt.xlabel("Number of search elements", fontsize=FONTSIZE_AXES)
plt.ylabel("Number of quantum operations", fontsize=FONTSIZE_AXES)
plt.plot(x_values, avg_naive_values, c="orange", ls="-", label="Naive multi-element search")
plt.plot(x_values, avg_smart_values, c="blue", ls="-", label="Optimal multi-element search")
plt.legend(fontsize=FONTSIZE_LEGEND, loc="upper left")
plt.xticks(list(range(1, 11)))
plt.grid()

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
plt.legend(fontsize=FONTSIZE_LEGEND, loc="upper left")
plt.grid()

# plt.title("Speed of quantum simulation of Grover's search")
plt.xlabel("Length of search string", fontsize=FONTSIZE_AXES)
plt.ylabel("Runtime in seconds", fontsize=FONTSIZE_AXES)

plt.savefig("plots/min_avg_max_runtime.png")
plt.show()

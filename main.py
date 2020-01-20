from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI
from runner import *
import matplotlib.pyplot as plt
import time

start_login = time.time()
# enable_account("58957ea5a48a801eb5af6adcae7776126c122c9d")
# qi = QuantumInspireAPI()
qi = None
print("Logged in to QI account ({} seconds)".format(str(time.time() - start_login)[:5]))\

SEARCH_TARGETS = [
    "000"[::-1],
    "100"[::-1],
]

SHOT_COUNT = 500

# whether to apply optimisation to our generated QASM
# performance improvement of ~20-50%
OPTIMISE = True

# MODES:
#   - normal: use toffoli gates and ancillary bits for max speed
#   - no toffoli: same as normal, but replace toffoli gates for 2-gate equivalent circuits. uses ancillary bits.
#   - crot: no ancillary bits or toffoli gates, but scales with 3^n gates for n bits
#   - fancy cnot: no ancillary bits or toffoli gates, scales 2^n
MODE = "normal"


# BOOL_EXPRESSION = "((a and b) and c) or ((not(a) and not(b)) and not(c))"
# BOOL_EXPRESSION = "((((((not(a) or not(b)) or not(c)) and " \
#                   "((a or not(b)) or c)) and " \
#                   "((a or b) or not(c))) and " \
#                   "((a or not(b)) or not(c))) and " \
#                   "((not(a) or b) or c))"

plt.figure()


# result_file = open("results/plot_data {}.txt".format(int(time.time())), "w")

# run_grover_search(qi, SEARCH_TARGETS, SHOT_COUNT, MODE, plot=True)

# for i in range(3, 10):
#     local_search_targets = ["1" * i]
#     print(local_search_targets)
#     runs = 10
#     avg = 0
#     for j in range(runs):
#         histogram_list, target_probs, non_target_prob, line_count, runtime = run_grover_search(qi, local_search_targets, SHOT_COUNT, MODE)
#         result_file.write("{}, {}, {}, {}\n".format(i, runtime, 1 - non_target_prob, line_count))
#         avg += runtime / runs
#     x_values.append(i)
#     y_values.append(avg)


# 4 IMPLEMENTATION LINE COUNT PLOT

# opt_norm_values = []
# unopt_norm_values = []
# opt_fancy_values = []
# unopt_fancy_values = []
#
# for i in range(3, 12):
#     x_values.append(i)
#     # opt_values.append(run_grover_search(qi, ["1" * i], SHOT_COUNT, MODE))
#     opt_norm = run_grover_search(qi, ["1" * i], SHOT_COUNT, "no toffoli")
#     opt_norm_values.append(opt_norm)
#     # unopt_values.append(run_grover_search(qi, ["1" * i], SHOT_COUNT, MODE, apply_optimisation=False))
#     unopt_norm = run_grover_search(qi, ["1" * i], SHOT_COUNT, "no toffoli", apply_optimisation=False)
#     unopt_norm_values.append(unopt_norm)
#     opt_fancy = run_grover_search(qi, ["1" * i], SHOT_COUNT, "fancy cnot")
#     opt_fancy_values.append(opt_fancy)
#     unopt_fancy = run_grover_search(qi, ["1" * i], SHOT_COUNT, "fancy cnot", apply_optimisation=False)
#     unopt_fancy_values.append(unopt_fancy)
#
# plt.title("Scaling of different CNOT implementations")
# plt.yscale("log")
# plt.xlabel("Length of search string")
# plt.ylabel("Number of quantum operations (approximate)")
# plt.plot(x_values, unopt_norm_values, c="orange", ls="-", label="Using n-3 ancillary bits")
# plt.plot(x_values, opt_norm_values, c="blue", ls="-", label="Using n-3 ancillary bits (optimised)")
# plt.plot(x_values, unopt_fancy_values, c="red", ls="-", label="Using no ancillary bits")
# plt.plot(x_values, opt_fancy_values, c="green", ls="-", label="Using no ancillary bits (optimised)")
# plt.legend()
#
# plt.show()


# SAT vs classical plot

# bool_expression = "(a and b)"
# x_values = []
# sat_values = []
# cl_values = []
# qubit_counts = []
#
# for i in range(3, 12):
#     x_values.append(i)
#     bool_expression = "(" + bool_expression + " and {})".format(chr(96+i))
#     print(bool_expression)
#     sat_val, qubit_count = run_grover_sat(qi, bool_expression, SHOT_COUNT, MODE)
#     sat_values.append(sat_val)
#     qubit_counts.append(qubit_count)
#     cl_values.append((2 ** i) * i)
#
# fig, ax1 = plt.subplots()
#
# plt.title("Scaling of classical vs quantum SAT solving")
# plt.yscale("log")
# ax1.set_xlabel("Number of boolean variables")
# ax1.set_ylabel("Number of operations (approximate)")
# ax1.plot(x_values, sat_values, c="blue", ls="-", label="SAT Solver using Grover (optimised)")
# ax1.plot(x_values, cl_values, c="red", ls="-", label="Classical (exhaustive) SAT Solver")
#
# ax2 = ax1.twinx()
# ax2.plot(x_values, qubit_counts, c="green", ls="--", label="Number of qubits required for Grover")
#
# ax1.legend()
# ax2.legend(loc="lower right")
#
# plt.show()


# Naive vs smart multi-search plot
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
multi_values = []

for i in range(1, len(searchables)):
    x_values.append(i)
    to_search = searchables[:i]
    naive_count = 0
    for t in to_search:
        naive_count += run_grover_search(qi, [t], SHOT_COUNT, "no toffoli")
    naive_values.append(naive_count)

    multi_count = run_grover_search(qi, to_search, SHOT_COUNT, "no toffoli")
    multi_values.append(multi_count)

plt.title("Naive vs optimal multi-element search")
plt.xlabel("Number of search elements")
plt.ylabel("Number of quantum operations (approximate)")
plt.plot(x_values, naive_values, c="orange", ls="-", label="Naive multi-element search")
plt.plot(x_values, multi_values, c="blue", ls="-", label="Optimal multi-element search")
plt.legend()

plt.show()
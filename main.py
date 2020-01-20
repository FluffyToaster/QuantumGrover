from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI
from runner import *
import time

start_login = time.time()
enable_account("58957ea5a48a801eb5af6adcae7776126c122c9d")
qi = QuantumInspireAPI()

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
BOOL_EXPRESSION = "((not(a) and not(b)) and not(c)) and not(d)"

run_grover_sat(qi, BOOL_EXPRESSION, SHOT_COUNT, MODE)


# import matplotlib.pyplot as plt
#
# plt.figure()
# x_values = []
# y_values = []
#
# result_file = open("results/plot_data {}.txt".format(int(time.time())), "w")

# run_grover_search(qi, SEARCH_TARGETS, SHOT_COUNT, MODE, plot=True)

# for i in range(3, 12):
#     local_search_targets = ["1" * i]
#     print(local_search_targets)
#     runs = 10
#     avg = 0
#     for j in range(runs):
#         histogram_list, target_probs, non_target_prob, line_count, runtime = run_grover(qi, local_search_targets, SHOT_COUNT, MODE)
#         result_file.write("{}, {}, {}, {}\n".format(i, runtime, 1 - non_target_prob, line_count))
#         avg += runtime / runs
#     x_values.append(i)
#     y_values.append(avg)

# result_file.close()
# plt.plot(x_values, y_values)

# plt.show()

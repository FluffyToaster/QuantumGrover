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

import matplotlib.pyplot as plt
import numpy as np

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
plt.plot(x_values, filtered_avgs, "b-")
plt.plot(x_values, mins, "g-")
plt.plot(x_values, maxs, "r-")
# plt.fill_between(x_values,
#                  np.subtract(np.array(filtered_avgs), np.array(stds)),
#                  np.array(filtered_avgs) + np.array(stds))

plt.show()

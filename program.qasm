# Single gates
# Pauli gates: X, Y, Z
# Hadamard H
# Rotation: Rx, Ry, Rz. Ex: Rx q[0], 3.14/4

# Two qubit gates
# CNOT

# Measurement
# Measure_x, Measure_y, Measure_z

# Start of program

# Demonstration: Making various configurations with only our chosen univ. gate set.

# X gate
Rx q[0], PI/1
# Y gate
Ry q[0], PI/1
# Z gate
Rz q[0], PI/1


# Bell State 00 + 11
# Rx q[0], PI/2
# CNOT q[0], q[1]

# Bell State 10 + 01
# Rx q[1], PI/1
# Rx q[0], PI/2
# CNOT q[0], q[1]

# Hadamard
# Ry q[0], PI/2
# Rx q[0], PI/1
# Ry q[0], PI/2
# Rx q[0], PI/1

# SWAP
Rx q[0], PI/1
CNOT q[0], q[1]
CNOT q[1], q[0]
CNOT q[0], q[1]
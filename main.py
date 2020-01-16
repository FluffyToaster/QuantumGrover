from quantuminspire.credentials import enable_account
from quantuminspire.api import QuantumInspireAPI
from runner import *

start_login = time.time()
enable_account("58957ea5a48a801eb5af6adcae7776126c122c9d")
qi = QuantumInspireAPI()

print("Logged in to QI account ({} seconds)".format(str(time.time() - start_login)[:5]))\

SEARCH_TARGETS = [
    "10101"[::-1],
    "10100"[::-1],
]

SHOT_COUNT = 10000

# whether to apply optimisation to our generated QASM
# performance improvement of ~20-50%
OPTIMISE = True

# MODES:
#   - normal: use toffoli gates and ancillary bits for max speed
#   - no toffoli: same as normal, but replace toffoli gates for 2-gate equivalent circuits. uses ancillary bits.
#   - crot: no ancillary bits or toffoli gates, but scales with 3^n gates for n bits
#   - fancy cnot: no ancillary bits or toffoli gates, scales 2^n
MODE = "fancy cnot"

histogram_list, target_probs, non_target_prob, line_count, runtime = run_grover(qi, SEARCH_TARGETS, SHOT_COUNT, MODE)


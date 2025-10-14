# Need to move from the venv or operational reference position to the Python folder at the bottom
import sys
sys.path.append(r"./py")
sys.path.append(r"../py")
sys.path.append(r"../../py")
sys.path.append(r"../../../py")

import tcp_protocol_server as tcs

HOST = 'localhost'
PORT = 9999

import numpy as np
import matplotlib.pyplot as plt
import time

A = np.array([[1,	0.00186692358465267,	0.00499986996220547,	3.11087460498839e-06],
              [0,	1.00327186436010,	-1.28817953710448e-07,	0.00500545193207790],
              [0,	0.747169921700842,	0.999947969310385,	0.00186692358465267],
              [0,	1.30945254573124,	-5.15548151936838e-05,	1.00327186436010]], dtype=float)

B = np.array([[0.000621774075159372],
              [0.000614690488247613],
              [0.248783930854796],
              [0.246008052850483]], dtype=float)

C = np.array([[1,	0,	0,	0],
              [0,	1,	0,	0]], dtype=float)

D = np.array([[0],
              [0]], dtype=float)

x = np.array([[0.031],
              [0.052],
              [0],
              [0]], dtype=float)

u = np.array([[0]], dtype=float)

y = np.array([[0],
              [0]], dtype=float)

max_iter = 3000
x_his = np.zeros((max_iter, 1))
y_his = np.zeros((max_iter, 2))

with tcs.tcp_server(HOST, PORT) as tcsp:
    tcsp.set_metric(False, 100)
    tcsp.set_sampleconst(False, 10)
    tcsp.set_printflag(False)

    for i in range(max_iter):
        stc = time.perf_counter_ns() / 1000000
        tcsp.send("R")
        y = C @ x + D @ u

        # save output result
        # print(y)
        x_his[i, 0] = i
        y_his[i, 0] = y[0, 0]
        y_his[i, 1] = y[1, 0]
        
        tcsp.send(y[0, 0])
        tcsp.send(y[1, 0])

        x = A @ x + B @ u

        _, u0 = tcsp.recv()
        u[0, 0] = u0
        edc = time.perf_counter_ns() / 1000000
        print(f"{edc - stc} ms runtime")

    tcsp.send("E")

fig, axes = plt.subplots(2, 1)

axes[0].plot(x_his, y_his[:,0])
axes[0].set_title('angle?')
axes[0].grid(True)

axes[1].plot(x_his, y_his[:,1])
axes[1].set_title('position?')
axes[1].grid(True)

fig.suptitle('plant output')
plt.tight_layout()
plt.savefig('plant output as sim.png')
    
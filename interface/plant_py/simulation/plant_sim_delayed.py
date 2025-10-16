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

A = np.array([[1, 7.46389157894123e-05, 0.000999994778562850, 2.48794432911939e-08],
              [0, 1.00013080714855, -5.16077182085482e-09, 0.00100004360202403],
              [0, 0.149280826123508, 0.999989557015481, 7.46389157894123e-05],
              [0, 0.261619743678534, -1.03217506940450e-05, 1.00013080714855]], dtype=float)

B = np.array([[2.48639864264349e-05],
              [2.45751039088325e-05],
              [0.0497284977084867],
              [0.0491511937811665]], dtype=float)

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
        tcsp.send("R")
        _, symb = tcsp.recv()

        y = C @ x + D @ u

        # save output result
        # print(y)
        x_his[i, 0] = i
        y_his[i, 0] = y[0, 0]
        y_his[i, 1] = y[1, 0]

        if symb == "ITR":
            tcsp.send(y[0, 0])
            tcsp.send(y[1, 0])
            _, u0 = tcsp.recv()
            u[0, 0] = u0
        print(u)
        x = A @ x + B @ u

    tcsp.send("E")

fig, axes = plt.subplots(2, 1)

axes[0].plot(x_his, y_his[:,0])
axes[0].set_title('position')
axes[0].grid(True)

axes[1].plot(x_his, y_his[:,1])
axes[1].set_title('angle')
axes[1].grid(True)

fig.suptitle('plant output')
plt.tight_layout()
plt.savefig('plant output with delayed control input as sim.png')


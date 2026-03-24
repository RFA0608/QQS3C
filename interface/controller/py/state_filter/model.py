import numpy as np
import control as ct

class sf:
    # sampling peroid
    ts = 0.1

    # system(state) matrix(state space linearlization - discrete model)
    A = np.zeros((4,4), dtype=float)
    B = np.zeros((4,1), dtype=float)
    C = np.zeros((2,4), dtype=float)
    D = np.zeros((2,1), dtype=float)

    # output gain K and observer gain L
    K = np.zeros((1,4), dtype=float)

    # estimation state
    es = np.zeros((4,1), dtype=float)

    # filter state
    fs_theta = np.zeros((1,2), dtype=float)
    fs_alpha = np.zeros((1,2), dtype=float)

    def __init__(self, ts):
        # write your continous time linear model
        A = np.array([[0, 0, 1, 0],
                      [0, 0, 0, 1],
                      [0, 149.275096865093, -0.0130994260613721, 0],
                      [0, 261.609107366662, -0.0129471071536817, 0]], dtype=float)
        B = np.array([[0],
                      [0],
                      [55.6948386963098],
                      [55.0472242928643]], dtype=float)
        C = np.array([[1, 0, 0, 0],
                      [0, 1, 0, 0],
                      [0, 0, 1, 0],
                      [0, 0, 0, 1]], dtype=float)
        D = np.array([[0],
                      [0],
                      [0],
                      [0]], dtype=float)
        sys_c = ct.ss(A, B, C, D)
        sys_d = sys_c.sample(ts, method='zoh')

        # save discretization value
        self.A = sys_d.A
        self.B = sys_d.B
        self.C = C
        self.D = D

        # for gain K dlqr parameters setting
        Q_k = np.array([[5, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]], dtype=float)
        R_k = np.array([[1]], dtype=float)
        K, Sk, Ek = ct.dlqr(self.A, self.B, Q_k, R_k)

        # save gain K and sampling period
        self.K = K
        self.ts = ts

    def ddt_filter(self, u, state, A):
        y = 1/(A*self.ts+2)*(2*A*u - 2*A*state[0, 0] - state[0, 1]*(A*self.ts - 2))

        state[0, 0] = u
        state[0, 1] = y

        return y, state

    def state_update(self, y):
        # estimation state using d/dt filter
        self.es[0, 0] = y[0, 0]
        self.es[1, 0] = y[1, 0]
        self.es[2, 0], self.fs_theta = self.ddt_filter(y[0, 0], self.fs_theta, 50)
        self.es[3, 0], self.fs_alpha = self.ddt_filter(y[1, 0], self.fs_alpha, 100)
        
        # save next state using state matrix
        # self.es = (self.A + self.B @ self.K) @ self.es

    def get_output(self):
        return -self.K @ self.es

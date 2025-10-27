import numpy as np
import control as ct

class ctrl:
    # system(state) matrix(state space linearlization - discrete model)
    A = np.zeros((4,4), dtype=float)
    B = np.zeros((4,1), dtype=float)
    C = np.zeros((2,4), dtype=float)
    D = np.zeros((2,1), dtype=float)

    # output gain K and observer gain L
    K = np.zeros((1, 4), dtype=float)
    L = np.zeros((4, 2), dtype=float)

    # observer controller state space model
    F = np.zeros((4,4), dtype=float)
    G = np.zeros((4,2), dtype=float)
    H = np.zeros((1,4), dtype=float)
    J = np.zeros((1,1), dtype=float) 

    # state and output
    xc = np.zeros((4,1), dtype=float)
    u = np.zeros((1,1), dtype=float)

    def __init__(self, ts):
        # write your continous time linear model
        A = np.array([[0, 0, 1, 0],
                      [0, 0, 0, 1],
                      [0, 149.275096865093, -0.0104427822555581, 0],
                      [0, 261.609107366662, -0.0103213545549121, 0]], dtype=float)
        B = np.array([[0],
                      [0],
                      [49.7275345502766],
                      [49.1493074043432]], dtype=float)
        C = np.array([[1, 0, 0, 0],
                      [0, 1, 0, 0]], dtype=float)
        D = np.array([[0],
                      [0]], dtype=float)
        sys_c = ct.ss(A, B, C, D)
        sys_d = sys_c.sample(ts, method='zoh')

        # save discretization value
        self.A = sys_d.A
        self.B = sys_d.B
        self.C = C
        self.D = D

        # for gain K dlqr parameters setting
        Q_k = np.array([[10, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]], dtype=float)
        R_k = np.array([[1]], dtype=float)
        K, Sk, Ek = ct.dlqr(self.A, self.B, Q_k, R_k)
        
        # for gain L dlqr parameters setting
        Q_l = np.array([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 100, 0],
                        [0, 0, 0, 10]], dtype=float)
        R_l = np.array([[1, 0],
                        [0, 1]], dtype=float)
        L, Sl, El = ct.dlqr(self.A.T, self.C.T, Q_l, R_l)

        # save gain K and L
        self.K = K
        self.L = L.T

        # make a controller state space matrix
        self.F = self.A - self.B @ self.K - self.L @ self.C
        self.G = self.L
        self.H = -self.K

        # ------------------------------------------------ #

        # set initial point of state
        x_init = np.array([[0],
                           [0],
                           [0],
                           [0]], dtype=float)
        
        # save initial point
        self.xc = x_init


    def state_update(self, y):
        # update state on temp variable
        xc_next = self.F @ self.xc + self.G @ y
        
        # save state
        self.xc = xc_next

    def get_output(self):
        return self.H @ self.xc
    
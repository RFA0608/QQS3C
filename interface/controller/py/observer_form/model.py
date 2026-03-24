import numpy as np
import control as ct

class obs:
    # sampling peroid
    ts = 0.1

    # system(state) matrix(state space linearlization - discrete model)
    A = np.zeros((4,4), dtype=float)
    B = np.zeros((4,1), dtype=float)
    C = np.zeros((2,4), dtype=float)
    D = np.zeros((2,1), dtype=float)

    # output gain K and observer gain L
    K = np.zeros((1,4), dtype=float)
    L = np.zeros((4,2), dtype=float)

    # observer controller state space model
    F = np.zeros((4,4), dtype=float)
    G = np.zeros((4,2), dtype=float)
    H = np.zeros((1,4), dtype=float)
    J = np.zeros((1,2), dtype=float) 

    # state and output
    x = np.zeros((4,1), dtype=float)
    u = np.zeros((1,1), dtype=float)

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
        self.ts = ts

        # for gain K dlqr parameters setting
        Q_k = np.array([[5000, 0, 0, 0],
                        [0, 400, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]], dtype=float)
        R_k = np.array([[1]], dtype=float)
        K, Sk, Ek = ct.dlqr(self.A, self.B, Q_k, R_k)
        
        # for gain L dlqr parameters setting
        Q_l = np.array([[1, 0, 0, 0],
                        [0, 1, 0, 0],
                        [0, 0, 500, 0],
                        [0, 0, 0, 100]], dtype=float)
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
        self.x = x_init

    def state_update(self, y):
        # update state on temp variable
        x_next = self.F @ self.x + self.G @ y
        
        # save state
        self.x = x_next

    def get_output(self):
        self.u = self.H @ self.x

        return self.u

class obs_q():
    # quantized level s for matrix and r for signal
    s = 1
    r = 1

    # gain of y and x 
    F = np.zeros((4,4), dtype=float)
    G = np.zeros((4,2), dtype=float)
    H = np.zeros((1,4), dtype=float)
    F_q = np.zeros((4,4), dtype=int)
    G_q = np.zeros((4,2), dtype=int)
    H_q = np.zeros((1,4), dtype=int)

    # state and input/output
    x_q = np.zeros((4,1), dtype=int)
    x = np.zeros((4,1), dtype=float)
    y_q = np.zeros((2,1), dtype=int)
    u_q = np.zeros((1,1), dtype=int)
    u = np.zeros((1,1), dtype=float)

    def __init__(self, F, G, H):
        self.F = F
        self.G = G
        self.H = H

    def set_level(self, r, s):
        self.r = r
        self.s = s

    def quantize(self):
        self.F_q = (self.s * self.F).astype(int)
        self.G_q = (self.s * self.G).astype(int)
        self.H_q = (self.s * self.H).astype(int)
    
    def state_update(self, x, y):
        # update state with quantization
        for i in range(2):
            self.y_q[i, 0] = int(self.r * y[i, 0])
        for i in range(4):
            self.x_q[i, 0] = int(self.r * x[i, 0])

        self.x_q = self.F_q @ self.x_q + self.G_q @ self.y_q
        self.x = self.x_q.astype(float) / self.r / self.s
        
        return self.x
    
    def get_output(self):
        self.u_q = self.H_q @ self.x_q
        self.u[0, 0] = float(self.u_q[0, 0]) / self.r / self.s / self.s

        return self.u

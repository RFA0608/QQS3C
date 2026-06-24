import numpy as np
import control as ct

class nobs:
    # hyperparams
    ts = 0.02
    alpha = np.array([[1.5, 0.4]], dtype=float)
    beta = np.array([[1.5, 0.4]], dtype=float)
    contractive_ratio = 0.6
    epsilon = 1

    Km = 0.042
    Kt = 0.042
    Rm = 7.5
    br = 1e-6
    bp = 5e-8
    mp = 0.024
    mr = 0.095
    l = 0.129/2
    r = 0.085
    Jr = mr*r**2/3
    Jp = mp*(2*l)**2/3
    g = 9.81
    

    # system(state) matrix only linear part
    A = np.zeros((4,4), dtype=float)
    B = np.zeros((4,1), dtype=float)

    # output gain K
    K = np.zeros((1,4), dtype=float)

    # state and output
    x = np.zeros((4,1), dtype=float)
    u = np.zeros((1,1), dtype=float)

    def __init__(self, ts):
        self.ts = ts

        # Linearlization part for control input
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
        sys_cl = ct.ss(A, B, C, D)
        sys_dl = sys_cl.sample(ts, method='zoh')

        # for gain K dlqr parameters setting
        Q_k = np.array([[50, 0, 0, 0],
                        [0, 4, 0, 0],
                        [0, 0, 1, 0],
                        [0, 0, 0, 1]], dtype=float)
        R_k = np.array([[1]], dtype=float)
        K, Sk, Ek = ct.dlqr(sys_dl.A, sys_dl.B, Q_k, R_k)
        self.K = K

        # nonlinear high-gain observer part
        self.epsilon = ts / np.log(1/self.contractive_ratio).item()

        A_c = np.array([[-self.alpha[0,0]/self.epsilon, 0, 1, 0],
                        [0, -self.beta[0,0]/self.epsilon, 0, 1],
                        [-self.alpha[0,1]/(self.epsilon**2), 0, 0, 0],
                        [0, -self.beta[0,1]/(self.epsilon**2), 0, 0]], dtype=float)
        
        B_c = np.array([[self.alpha[0,0]/self.epsilon, 0],
                        [0, self.beta[0,0]/self.epsilon],
                        [self.alpha[0,1]/(self.epsilon**2), 0],
                        [0, self.beta[0,1]/(self.epsilon**2)]], dtype=float)
        C_c = np.array([[1, 0, 0, 0],
                      [0, 1, 0, 0],
                      [0, 0, 1, 0],
                      [0, 0, 0, 1]], dtype=float)
        D_c = np.array([[0, 0],
                      [0, 0],
                      [0, 0],
                      [0, 0]], dtype=float)
        
        sys_c = ct.ss(A_c, B_c, C_c, D_c)
        sys_d = sys_c.sample(ts, method='zoh')

        self.A = sys_d.A
        self.B = sys_d.B

        # set initial point of state
        x_init = np.array([[0],
                           [0],
                           [0],
                           [0]], dtype=float)
        
        # save initial point
        self.x = x_init

    def state_update(self, y, v):
        x_next = self.A @ self.x + self.B @ y

        u = (self.Kt / self.Rm) * (v - self.Km * self.x[2,0])
        term_1 = u - self.br * self.x[2,0] - 2 * self.Jp * np.sin(self.x[1,0]) * np.cos(self.x[1,0]) * self.x[2,0] * self.x[3,0] - self.mp * self.l * self.r * np.sin(self.x[1,0]) * self.x[3,0]**2
        term_2 = -self.bp * self.x[3,0] + self.Jp * np.sin(self.x[1,0]) * np.cos(self.x[1,0]) * self.x[2,0]**2 + self.mp * self.g * self.l * np.sin(self.x[1,0])
        denominator = self.Jp * (self.Jr + self.Jp * np.sin(self.x[1,0])**2) - self.mp**2 * self.l**2 * self.r**2 * np.cos(self.x[1,0])**2

        f3 = (self.ts * (self.Jp * term_1 - (-self.mp * self.l * self.r * np.cos(self.x[1,0])) * term_2) / denominator).item()
        f4 = (self.ts * (-(-self.mp * self.l * self.r * np.cos(self.x[1,0])) * term_1 + (self.Jr + self.Jp * np.sin(self.x[1,0])**2) * term_2) / denominator).item()

        x_next = x_next + np.array([[0.0],
                                    [0.0],
                                    [f3],
                                    [f4]], dtype=float)

        # save state
        self.x = x_next


    def get_output(self):
        self.u = -self.K @ self.x

        self.u = np.clip(self.u, -15.0, 15.0)
        return self.u

class narx:
    # nobs instance
    nobs = any

    # hyperparams of time horizon N
    N = 10

    # trajectory of y and u / old is little index
    y_seq = any
    u_seq = any

    def __init__(self, nobs, N):
        self.N = N

        self.y_seq = np.zeros((self.N, 2), dtype=float)
        self.u_seq = np.zeros((self.N, 1), dtype=float)

        self.nobs = nobs

    def mem_update(self, y, u):
        for i in range(self.N-1):
            self.y_seq[i, :] = self.y_seq[i+1, :]
            self.u_seq[i, :] = self.u_seq[i+1, :]

        self.y_seq[self.N-1, :] = y.reshape(1,2)
        self.u_seq[self.N-1, :] = u.reshape(1,1)

    def get_output(self):
        self.nobs.x = np.zeros((4,1), dtype=float)

        for i in range(self.N):
            self.nobs.state_update(self.y_seq[i,:].reshape(2,1), self.u_seq[i,:].reshape(1,1))

        u = self.nobs.get_output();
        return u

        



    


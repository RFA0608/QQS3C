import numpy as np
import control as ct

class rotpen:
    # system(state) matrix(state space linearlization - discrete model)
    A = np.zeros((4,4), dtype=float)
    B = np.zeros((4,1), dtype=float)
    C = np.zeros((2,4), dtype=float)
    D = np.zeros((2,1), dtype=float)

    # state and output
    xp = np.zeros((4,1), dtype=float)
    y = np.zeros((2,1), dtype=float)

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

        # ------------------------------------------------ #

        # set initial point of state
        x_init = np.array([[0],
                           [0],
                           [0],
                           [0]], dtype=float)
        
        # save initial point
        self.xp = x_init

    def set_init(self, x_init):
        self.xp = x_init

    def state_update(self, u):
        # update state on temp variable
        xp_next = self.A @ self.xp + self.B @ u
        
        # save state
        self.xp = xp_next

    def get_output(self):
        return self.C @ self.xp
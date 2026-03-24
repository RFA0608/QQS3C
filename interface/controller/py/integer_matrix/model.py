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
    
class intmat():
    # sampling peroid
    ts = 0.1

    # observer controller state space model
    F = np.zeros((4,4), dtype=float)
    G = np.zeros((4,2), dtype=float)
    H = np.zeros((1,4), dtype=float)
    J = np.zeros((2,1), dtype=float) 

    # gain of which convert F-RH's pole to integer 
    R = np.zeros((4,1), dtype=float)

    # converted to int model
    F_cv = np.zeros((4,4), dtype=float)
    G_cv = np.zeros((4,2), dtype=float)
    H_cv = np.zeros((1,4), dtype=float)
    R_cv = np.zeros((4,1), dtype=float) 

    # state and output
    x = np.zeros((4,1), dtype=float)
    u = np.zeros((1,1), dtype=float)

    def __init__(self, F, G, H, J, ts):
        self.F = F
        self.G = G
        self.H = H
        self.J = J
        self.ts = ts

        # find gain R which convert F-RH's pole to integer
        pole = np.array([[0, 1, 2, -1]])
        R = ct.place(self.F.T, self.H.T, pole).T
        
        # save gain R
        self.R = R
    
        # # This section doesn't support on python-control library
        # # So, you change on MATLAB and save manualy
        # # find canonical model transformed matrix T
        # sys = ct.ss((F-R@H), G, H, J)
        # csys, T = ct.canonical_form(sys, form='reachable')

        # # save converted form
        # self.F_cv = T@(F-R@H)/T
        # self.R_cv = T@R
        # self.G_cv = T@G
        # self.H_cv = H/T

        # save converted matrix manualy from MATLAB
        # you can found the file name of "transpose_matrix2int" on /interface/controller/py/tools folder
        # copy and paste observer state matrix F, G, H to there, get and write below invertible matrix T
        T = np.array([[1.08314828520927, -1.66955395965037, -0.00236729459240089, 0.00841047244267525],
                      [-12.3192475520305, 21.2280825206628, 1.11207418021025, -2.55670558562088],
                      [-6.55696463635024, 10.9797588171927, 0.590938554977826, -1.32609684315751],
                      [6.17193488024287, -10.6209349231961, -0.557028488424479, 1.27749537728892]])
        
        self.F_cv = (T@(F-R@H)@np.linalg.inv(T)).round()
        self.R_cv = T@R
        self.G_cv = T@G
        self.H_cv = H@np.linalg.inv(T)
        
    def state_update(self, y, u):
        # update state on temp variable
        x_next = self.F_cv @ self.x + self.G_cv @ y + self.R_cv @ u

        # save state
        self.x = x_next

    def get_output(self):
        self.u = self.H_cv @ self.x

        return self.u

class intmat_q():
    # quantized level s for matrix and r for signal
    s = 1
    r = 1

    # gain of y and x 
    F = np.zeros((4,4), dtype=float)
    G = np.zeros((4,2), dtype=float)
    H = np.zeros((1,4), dtype=float)
    R = np.zeros((4,1), dtype=float) 
    F_q = np.zeros((4,4), dtype=int)
    G_q = np.zeros((4,2), dtype=int)
    H_q = np.zeros((1,4), dtype=int)
    R_q = np.zeros((4,1), dtype=int) 

    # state and input/output
    x_q = np.zeros((4,1), dtype=int)
    y_q = np.zeros((2,1), dtype=int)
    u_q = np.zeros((1,1), dtype=int)
    u = np.zeros((1,1), dtype=float)

    def __init__(self, F_cv, G_cv, H_cv, R_cv):
        self.F = F_cv
        self.G = G_cv
        self.H = H_cv
        self.R = R_cv

    def set_level(self, r, s):
        self.r = r
        self.s = s

    def quantize(self):
        self.F_q = (self.F).astype(int)
        self.G_q = (self.s * self.G).astype(int)
        self.H_q = (self.s * self.H).astype(int)
        self.R_q = (self.s * self.R).astype(int)  

    def state_update(self, y, u):
        # update state with quantization
        for i in range(2):
            self.y_q[i, 0] = int(self.r * y[i, 0])
        for i in range(1):
            self.u_q[i, 0] = int(self.r * u[i, 0])

        self.x_q = self.F_q @ self.x_q + self.G_q @ self.y_q + self.R_q @ self.u_q

    def get_output(self):
        self.u_q = self.H_q @ self.x_q
        self.u[0, 0] = float(self.u_q[0, 0]) / self.r / self.s / self.s

        return self.u

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
    
class fs():
    # gain of x
    H = np.zeros((1,4), dtype=float)

    # output
    u = np.zeros((1,1), dtype=float)

    def __init__(self, H):
        self.H = H

    def get_output(self, x):
        self.u = self.H @ x;

        return self.u
    
class fs_q():
    # quantized level s for matrix and r for signal
    s = 1
    r = 1

    # gain of x
    H = np.zeros((1,4), dtype=float)
    H_q = np.zeros((1,4), dtype=int)

    # input/output
    x_q = np.zeros((4,1), dtype=int)
    x = np.zeros((4,1), dtype=float)
    u_q = np.zeros((1,1), dtype=int)
    u = np.zeros((1,1), dtype=float)

    def __init__(self, H):
        self.H = H

    def set_level(self, r, s):
        self.r = r
        self.s = s

    def quantize(self):
        self.H_q = (self.s * self.H).astype(int)

    def get_output(self, x):
        for i in range(4):
            self.x_q[i, 0] = int(self.r * x[i, 0])

        self.u_q = self.H_q @ self.x_q
        
        self.u[0,0] = float(self.u_q[0, 0]) / self.r / self.s

        return self.u

from numpy.linalg import matrix_rank, eigvals

class arx():
    # observer controller state space model
    F = np.zeros((4,4), dtype=float)
    G = np.zeros((4,2), dtype=float)
    H = np.zeros((1,4), dtype=float)
    J = np.zeros((1,1), dtype=float)

    # gain for coordination transform
    L = np.zeros((4,1), dtype=float)

    # sequence of y and u like y0, y1, ...,y3 and u0, ...,u3
    # every y is column vector but save is row vector
    Ys = np.zeros((4,2), dtype=float)
    Us = np.zeros((4,1), dtype=float)

    # gain of y sequence and u sequence
    HG = np.zeros((4,2), dtype=float)
    HL = np.zeros((4,1), dtype=float)

    # output
    u = np.zeros((1,1), dtype=float)

    def __init__(self, F, G, H, J):
        # save original controller's state matrix
        self.F = F
        self.G = G
        self.H = H
        self.J = J
        
        O_matrix = ct.obsv(F, H)
        rank = matrix_rank(O_matrix)
        if rank != 4:
            is_obs = 0
            print(f"This controller is not observable")
        else:
            is_obs = 1
            
            # all desired_poles set to zero
            desired_poles = np.zeros(4)

            # calc L, which is gain that F-LH can be nilpotent
            L = ct.place_acker(self.F.T, self.H.T, desired_poles)

            # save gain L
            self.L[0, 0] = L[0]
            self.L[1, 0] = L[1]
            self.L[2, 0] = L[2]
            self.L[3, 0] = L[3]
            
            # validation of gain L
            eigenvalues = eigvals(self.F - self.L @self.H)
            print(f"eigenvalue of F - LH:\n {eigenvalues}")

            # calc H(F-LH)^3G ... HG and H(F-LH)^3L ... HL
            self.HG[0,:] = (self.H @ (self.F - self.L @ self.H) @ (self.F - self.L @ self.H) @ (self.F - self.L @ self.H) @ self.G)
            self.HG[1,:] = (self.H @ (self.F - self.L @ self.H) @ (self.F - self.L @ self.H) @ self.G)
            self.HG[2,:] = (self.H @ (self.F - self.L @ self.H) @ self.G)    
            self.HG[3,:] = (self.H @ self.G)   

            self.HL[0,:] = (self.H @ (self.F - self.L @ self.H) @ (self.F - self.L @ self.H) @ (self.F - self.L @ self.H) @ self.L)
            self.HL[1,:] = (self.H @ (self.F - self.L @ self.H) @ (self.F - self.L @ self.H) @ self.L)
            self.HL[2,:] = (self.H @ (self.F - self.L @ self.H) @ self.L)    
            self.HL[3,:] = (self.H @ self.L)

    def mem_update(self, Yn, Un):
        # i = 0 is oldest value
        for i in range(3):
            self.Ys[i,:] = self.Ys[(i+1),:]
            self.Us[i,:] = self.Us[(i+1),:]

        # new value input in i = 3
        self.Ys[3,:] = Yn.T
        self.Us[3,:] = Un

    def get_output(self):
        self.u[0, 0] = 0

        for i in range(4):
            self.u = self.u + self.HG[i,:] @ self.Ys[i,:].T + self.HL[i,:] @ self.Us[i,:]
        
        return self.u
    
class arx_q():
    # quantized level s for matrix and r for signal
    s = 1
    r = 1

    # sequence of y and u like y0, y1, ...,y3 and u0, ...,u3
    # every y is column vector but save is row vector
    Ys_q = np.zeros((4,2), dtype=int)
    Us_q = np.zeros((4,1), dtype=int)

    # gain of y sequence and u sequence
    HG = np.zeros((4,2), dtype=float)
    HL = np.zeros((4,1), dtype=float)
    HG_q = np.zeros((4,2), dtype=int)
    HL_q = np.zeros((4,1), dtype=int)

    # output
    u_q = np.zeros((1,1), dtype=int)
    u = np.zeros((1,1), dtype=float)

    def __init__(self, HG, HL):
        self.HG = HG
        self.HL = HL

    def set_level(self, r, s):
        self.r = r
        self.s = s

    def quantize(self):
        self.HG_q = (self.s * self.HG).astype(int)
        self.HL_q = (self.s * self.HL).astype(int)

    def mem_update(self, Yn, Un):
        # i = 0 is oldest value
        for i in range(3):
            self.Ys_q[i,:] = self.Ys_q[(i+1),:]
            self.Us_q[i,:] = self.Us_q[(i+1),:]

        # new value input in i = 3
        self.Ys_q[3,:] = (self.r * Yn.T).astype(int)
        self.Us_q[3,:] = (self.r * Un).astype(int)

    def get_output(self):
        self.u_q[0,0] = 0

        for i in range(4):
            self.u_q = self.u_q + self.HG_q[i,:] @ self.Ys_q[i,:].T + self.HL_q[i,:] @ self.Us_q[i,:]
        
        self.u[0,0] = float(self.u_q[0, 0]) / self.r / self.s

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
        T = np.array([[1.08298117367527, -1.68154748826889, -0.00233914245960275, 0.00849834019672862],
                      [-12.3537090165341, 21.4090792063878, 1.11583734511801, -2.57875666750599],
                      [-6.57440240290518, 11.0728803774811, 0.592848488851846, -1.33743052540943],
                      [6.18914661548333, -10.7115627543182, -0.558907686374587, 1.28851436364236]])
        
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
    x = np.zeros((4,1), dtype=float)
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
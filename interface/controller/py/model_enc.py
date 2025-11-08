import numpy as np
from openfhe import *

class crypto():
    # cryptocontext for encryption
    paramters = any
    crypto_context = any

    # key_pair for encrption
    key_pair = any

    def __init__(self):
        # parameter setting
        self.parameters = CCParamsBFVRNS()
        self.parameters.SetRingDim(4096)
        self.parameters.SetPlaintextModulus(4294008833)
        self.parameters.SetMultiplicativeDepth(2)
        self.parameters.SetSecurityLevel(SecurityLevel.HEStd_NotSet)
        
        # crypto context setting
        self.crypto_context = GenCryptoContext(self.parameters)
        self.crypto_context.Enable(PKESchemeFeature.PKE)
        self.crypto_context.Enable(PKESchemeFeature.KEYSWITCH)
        self.crypto_context.Enable(PKESchemeFeature.LEVELEDSHE)
        
        # key setting
        self.key_pair = self.crypto_context.KeyGen()
        self.crypto_context.EvalMultKeyGen(self.key_pair.secretKey)
        self.crypto_context.EvalRotateKeyGen(self.key_pair.secretKey, [1, 2, 3, 4])

    def get_crypto(self):
        return self.crypto_context

    def enc_vector(self, vec):
        # make plaintext with packing
        plaintext = self.crypto_context.MakePackedPlaintext(vec)
        
        # make ciphertext with encrypter
        ciphertext = self.crypto_context.Encrypt(self.key_pair.publicKey, plaintext)

        return ciphertext
    
    def dec_ciphertext(self, ciphertext):
        # make plaintext with decrypter
        plaintext = self.crypto_context.Decrypt(ciphertext, self.key_pair.secretKey)

        # make vecter(list) with unpacking
        vector = plaintext.GetPackedValue()

        return vector
    
class enc_for_fs():
    crypto_class = any

    # quantization level
    r = 1000
    s = 1000

    # gain of x
    H_q = np.zeros((1,4), dtype=int)

    # encrypted gain
    H_enc = any

    # encrypted state
    x_enc = any

    def __init__(self, crypto_class, H_q):
        self.crypto_class = crypto_class
        self.H_q = H_q
        
        vec = [-1, -1, -1, -1]
        # encryption H_q value only one packing
        for i in range(4):
            vec[i] = H_q[0, i]

        self.H_enc = self.crypto_class.enc_vector(vec)

    def set_level(self, r, s):
        self.r = r
        self.s = s
        
    def enc_signal(self, x):
        vec = list()
        for i in range(4):
            vec.append(int(x[i, 0] * self.r))

        self.x_enc = self.crypto_class.enc_vector(vec)

        return self.x_enc
    
    def dec_signal(self, ciphertext):
        vec = self.crypto_class.dec_ciphertext(ciphertext)

        return vec[0]
    
class fs_enc():
    # for encrypted calculation (only crypto context do not save crypto class)
    crypto_context = any 
    
    # encrypted gain
    H_enc = any

    def __init__(self, crypto_context, H_enc):
        self.crypto_context = crypto_context
        self.H_enc = H_enc

    def get_output(self, x_enc):
        ciphertext_mul = any

        ciphertext_mul = self.crypto_context.EvalMult(self.H_enc, x_enc)

        ciphertext_rot = ciphertext_mul
        ciphertext_result = ciphertext_mul

        for i in range(3):
            ciphertext_rot = self.crypto_context.EvalRotate(ciphertext_rot, 1)
            ciphertext_result = self.crypto_context.EvalAdd(ciphertext_result, ciphertext_rot)

        return ciphertext_result
    
class enc_for_obs():
    crypto_class = any

    # quantization level
    r = 1000
    s = 1000

    # gain of x and y
    F_q = np.zeros((4,4), dtype=int)
    G_q = np.zeros((4,2), dtype=int)
    H_q = np.zeros((1,4), dtype=int)

    # encrypted gain
    F_enc = []
    G_enc = []
    H_enc = []

    # encrypted state
    x_enc = []
    x_dec = np.zeros((4,1), dtype=float)
    y_enc = []
    u_dec = np.zeros((1,1), dtype=float)

    def __init__(self, crypto_class, F_q, G_q, H_q):
        self.crypto_class = crypto_class
        self.F_q = F_q
        self.G_q = G_q
        self.H_q = H_q

        vec = [-1, -1, -1, -1]
        # encryption and packgin every column vec
        # encryption F_q
        for i in range(4):
            vec[0] = F_q[0, i]
            vec[1] = F_q[1, i]
            vec[2] = F_q[2, i]
            vec[3] = F_q[3, i]
            self.F_enc.append(self.crypto_class.enc_vector(vec))
        # encryption G_q
        for i in range(2):
            vec[0] = G_q[0, i]
            vec[1] = G_q[1, i]
            vec[2] = G_q[2, i]
            vec[3] = G_q[3, i]
            self.G_enc.append(self.crypto_class.enc_vector(vec))
        # encryption H_q
        vec[1] = 0
        vec[2] = 0
        vec[3] = 0
        for i in range(4):
            vec[0] = H_q[0, i]
            self.H_enc.append(self.crypto_class.enc_vector(vec))
        # encryption componentwise of x and y
        # encryption x_init
        for i in range(4):
            vec[0] = 0
            self.x_enc.append(self.crypto_class.enc_vector(vec))
        # encryption y_init
        for i in range(2):
            vec[0] = 0
            self.y_enc.append(self.crypto_class.enc_vector(vec))

    def set_level(self, r, s):
        self.r = r
        self.s = s

    def enc_signal(self, x, y):
        vec = [0, 0, 0, 0]
        for i in range(4):
            for j in range(4):
                vec[j] = int(x[i, 0] * self.r)
            self.x_enc[i] = self.crypto_class.enc_vector(vec)
        
        for i in range(2):
            for j in range(4):
                vec[j] = int(y[i, 0] * self.r)
            self.y_enc[i] = self.crypto_class.enc_vector(vec)

        return self.x_enc, self.y_enc

    def dec_signal(self, ciphertext_x, ciphertext_u):
        vec = self.crypto_class.dec_ciphertext(ciphertext_x)
        for i in range(4):
            self.x_dec[i, 0] = vec[i]

        vec = self.crypto_class.dec_ciphertext(ciphertext_u)
        self.u_dec[0, 0] = vec[0]

        return self.x_dec, self.u_dec
    
class obs_enc():
    # for encrypted calculation (only crypto context do not save crypto class)
    crypto_context = any 

    # encrypted gain    
    F_enc = []
    G_enc = []
    H_enc = []

    def __init__(self, crypto_context, F_enc, G_enc, H_enc):
        self.crypto_context = crypto_context
        self.F_enc = F_enc
        self.G_enc = G_enc
        self.H_enc = H_enc

    def get_output(self, x_enc, y_enc):
        ciphertext_x_mul = []
        ciphertext_u_mul = []
        
        for i in range(4):
            ciphertext_x_mul.append(self.crypto_context.EvalMult(self.F_enc[i], x_enc[i]))

        for i in range(2):
            ciphertext_x_mul.append(self.crypto_context.EvalMult(self.G_enc[i], y_enc[i]))

        for i in range(4):
            ciphertext_u_mul.append(self.crypto_context.EvalMult(self.H_enc[i], x_enc[i]))

        
        ciphertext_x_add = ciphertext_x_mul[0]
        ciphertext_u_add = ciphertext_u_mul[0]

        for i in range(5):
            ciphertext_x_add = self.crypto_context.EvalAdd(ciphertext_x_add, ciphertext_x_mul[i+1])

        for i in range(3):
            ciphertext_u_add = self.crypto_context.EvalAdd(ciphertext_u_add, ciphertext_u_mul[i+1])

        return ciphertext_x_add, ciphertext_u_add

class enc_for_arx():
    crypto_class = any

    # quantization level
    r = 1000
    s = 1000

    # gain of y sequence and u sequence
    HG_q = np.zeros((4,2), dtype=int)
    HL_q = np.zeros((4,1), dtype=int)

    # encrypted gain that packed and encrypted like PQ_enc[0] = {HG_q[0, 0], HG_q[0, 1], HL_q[0, 0]}
    PQ_enc = []

    # encrypted signal sequence that packed and encrypted like S_enc[0] = {y[0, 0], y[1, 0], u[0, 0]}
    S_enc = any
    Z_enc = []

    def __init__(self, crypto_class, HG_q, HL_q):
        self.crypto_class = crypto_class
        self.HG_q = HG_q
        self.HL_q = HL_q

        vec = [-1, -1, -1]
        # encryption HG_q, HL_q value like enc(pack{HG_q[0, 0], HG_q[0, 1], HL_q[0, 0]})
        for i in range(4):
            vec[0] = HG_q[i, 0]
            vec[1] = HG_q[i, 1]
            vec[2] = HL_q[i, 0]
            
            self.PQ_enc.append(self.crypto_class.enc_vector(vec))
            
        # for first zero padding of memory
        for i in range(4):
            vec[0] = 0
            vec[1] = 0
            vec[2] = 0
            
            self.Z_enc.append(self.crypto_class.enc_vector(vec))

    def set_level(self, r, s):
        self.r = r
        self.s = s
        
    def enc_signal(self, y, u):
        vec = list()
        vec.append(int(y[0, 0] * self.r))
        vec.append(int(y[1, 0] * self.r))
        vec.append(int(u[0, 0] * self.r))

        self.S_enc = self.crypto_class.enc_vector(vec)

        return self.S_enc

    def dec_signal(self, ciphertext):
        vec = self.crypto_class.dec_ciphertext(ciphertext)

        return vec[0]
            
class arx_enc():
    # for encrypted calculation (only crypto context do not save crypto class)
    crypto_context = any 

    # encrypted gain that packed and encrypted like PQ_enc[0] = {HG_q[0, 0], HG_q[0, 1], HL_q[0, 0]}
    PQ_enc = []

    # encrypted signal sequence that packed and encrypted like S_enc[0] = {y[0, 0], y[1, 0], u[0, 0]}
    S_enc = []

    def __init__(self, crypto_context, PQ_enc, Z_enc):
        self.crypto_context = crypto_context
        self.PQ_enc = PQ_enc
        self.S_enc = Z_enc

    def mem_update(self, enc_signal):
        self.S_enc.pop(0)
        self.S_enc.append(enc_signal)

    def get_output(self):
        ciphertext_mul = []
        
        for i in range(4):
            ciphertext_mul.append(self.crypto_context.EvalMult(self.PQ_enc[i], self.S_enc[i]))
        
        ciphertext_add = ciphertext_mul[0]

        for i in range(3):
            ciphertext_add = self.crypto_context.EvalAdd(ciphertext_add, ciphertext_mul[i+1])

        ciphertext_rot = ciphertext_add
        ciphertext_result = ciphertext_add

        for i in range(2):
            ciphertext_rot = self.crypto_context.EvalRotate(ciphertext_rot, 1)
            ciphertext_result = self.crypto_context.EvalAdd(ciphertext_result, ciphertext_rot)

        return ciphertext_result

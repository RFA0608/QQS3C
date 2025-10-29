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
        self.parameters.SetPlaintextModulus(4294475777)
        self.parameters.SetMultiplicativeDepth(3)
        
        # crypto context setting
        self.crypto_context = GenCryptoContext(self.parameters)
        self.crypto_context.Enable(PKESchemeFeature.PKE)
        self.crypto_context.Enable(PKESchemeFeature.KEYSWITCH)
        self.crypto_context.Enable(PKESchemeFeature.LEVELEDSHE)

        # key setting
        self.key_pair = self.crypto_context.KeyGen()
        self.crypto_context.EvalMultKeyGen(self.key_pair.secretKey)
        self.crypto_context.EvalRotateKeyGen(self.key_pair.secretKey, [1, 2])

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
    
class enc_for_system():
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
        
    def enc_signal(self, y_q, u_q):
        vec = list()
        vec.append(int(y_q[0, 0] * self.r))
        vec.append(int(y_q[1, 0] * self.r))
        vec.append(int(u_q[0, 0] * self.r))

        self.S_enc = self.crypto_class.enc_vector(vec)

        return self.S_enc

    def dec_signal(self, ciphertext):
        vec = self.crypto_class.dec_ciphertext(ciphertext)

        return vec[0]
            
class ctrl_enc():
    # for encrypted calculation (only crypto context do not save crypto class)
    crypto = any 

    # encrypted gain that packed and encrypted like PQ_enc[0] = {HG_q[0, 0], HG_q[0, 1], HL_q[0, 0]}
    PQ_enc = []

    # encrypted signal sequence that packed and encrypted like S_enc[0] = {y[0, 0], y[1, 0], u[0, 0]}
    S_enc = []

    def __init__(self, crypto, PQ_enc, Z_enc):
        self.crypto = crypto
        self.PQ_enc = PQ_enc
        self.S_enc = Z_enc

    def mem_update(self, enc_signal):
        self.S_enc.pop(0)
        self.S_enc.append(enc_signal)

    def get_output(self):
        ciphertext_mul = []
        
        for i in range(4):
            ciphertext_mul.append(self.crypto.EvalMult(self.PQ_enc[i], self.S_enc[i]))
        
        ciphertext_add = ciphertext_mul[0]

        for i in range(3):
            ciphertext_add = self.crypto.EvalAdd(ciphertext_add, ciphertext_mul[i+1])

        ciphertext_rot = ciphertext_add
        ciphertext_result = ciphertext_add

        for i in range(2):
            ciphertext_rot = self.crypto.EvalRotate(ciphertext_rot, 1)
            ciphertext_result = self.crypto.EvalAdd(ciphertext_result, ciphertext_rot)

        return ciphertext_result
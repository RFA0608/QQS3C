import numpy as np
from openfhe import *

class crypto():
    # cryptocontext for encryption
    paramters = any
    crypto_context = openfhe.CryptoContext

    # key_pair for encrption
    key_pair = openfhe.KeyPair

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
    crypto_class = crypto

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
    crypto_context = openfhe.CryptoContext 
    
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

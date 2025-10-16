#include <iostream>
#include <vector>
#include <cmath>
#include "seal/seal.h"

using namespace std;
using namespace seal;

int main()
{
    int poly_degree = 8192;
    int plain_modulus = 36;

    EncryptionParameters parms(scheme_type::bgv);
    size_t poly_modulus_degree = (size_t)poly_degree;
    parms.set_poly_modulus_degree(poly_modulus_degree);
    parms.set_coeff_modulus(CoeffModulus::BFVDefault(poly_modulus_degree));
    parms.set_plain_modulus(PlainModulus::Batching(poly_modulus_degree, plain_modulus));
    SEALContext context(parms);

    cout << "poly degree: " << parms.poly_modulus_degree() << endl;
    cout << "plain modulus: " << parms.plain_modulus().value() << endl;
    cout << "cipher modulus: ";
    for(size_t i = 0; i < parms.coeff_modulus().size() - 1; i++)
    {
        if(i != (parms.coeff_modulus().size() - 2))
        {
            cout << parms.coeff_modulus()[i].value() << ", ";
        }
        else
        {
            cout << parms.coeff_modulus()[i].value();
        }
    }
    cout << endl << endl;

    KeyGenerator keygen(context);
    SecretKey secret_key = keygen.secret_key();
    PublicKey public_key;
    keygen.create_public_key(public_key);
    RelinKeys relin_keys;
    keygen.create_relin_keys(relin_keys);
    Encryptor encryptor(context, public_key);
    Evaluator evaluator(context);
    Decryptor decryptor(context, secret_key);
    
    BatchEncoder batch_encoder(context);
    size_t slot_count = batch_encoder.slot_count();
    vector<int64_t> pod_matrix(slot_count, 0LL);
    pod_matrix[0] = powl(10, 5); // 

    int iter = 1000;

    cout << "test set" << endl;
    cout << "max_iter: " << iter;
    cout << " | mult result: " << powl(pod_matrix[0], 2) << endl << endl;

    for(int i = 0; i < iter; i++)
    {
        Plaintext x_plain;
        batch_encoder.encode(pod_matrix, x_plain);

        Ciphertext x_cipher;
        encryptor.encrypt(x_plain, x_cipher);
        Ciphertext x_squared;
        evaluator.square(x_cipher, x_squared);

        Plaintext decrypted_result;
        decryptor.decrypt(x_squared, decrypted_result);
        vector<int64_t> pod_result;
        batch_encoder.decode(decrypted_result, pod_result);

        if(pod_result[0] != (pod_matrix[0] * pod_matrix[0]))
        {
            cout << "HE calc result: " << pod_result[0] << endl;
            cout << "Original calc result: " << (pod_matrix[0] * pod_matrix[0]) << endl;
            break;
        }
        else
        {
            if(i == iter - 1)
            {
                cout << "clearly good" << endl;
            }
        }
    }
    
    return 0;
}
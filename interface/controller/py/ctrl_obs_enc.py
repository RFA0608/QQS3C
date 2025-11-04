# get tcp_protocol description (vscode[debuger] launched at root directory)
import sys
sys.path.append(r"./py")
import tcp_protocol_client as tcc

# init tcp host and port
HOST = 'localhost'
PORT = 9999

# get model description
import model
import model_enc

# get other tools
import numpy as np
import time

def obs_encrypted():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.025
    run_signal = True

    # get model from model description file
    obs = model.obs(sampling_time)
    obs_q = model.obs_q(obs.F, obs.G, obs.H)

    # set quantized level and quantize matrix
    obs_q.set_level(1000, 1000)
    obs_q.quantize()

    # get crypto model from model_enc
    crypto_cl = model_enc.crypto()
    enc_4_obs = model_enc.enc_for_obs(crypto_cl, obs_q.F_q, obs_q.G_q, obs_q.H_q)
    enc_4_obs.set_level(obs_q.r, obs_q.s)
    obs_enc = model_enc.obs_enc(crypto_cl.crypto_context, enc_4_obs.F_enc, enc_4_obs.G_enc, enc_4_obs.H_enc)

    # input/output initialization
    x = np.array([[0],
                  [0],
                  [0],
                  [0]], dtype=float)
    y = np.array([[0],
                  [0]], dtype=float)
    u = np.array([[0]], dtype=float)

    with tcc.tcp_client(HOST, PORT) as tccp:
        while run_signal:
            # running signal send for controller
            _, signal = tccp.recv()

            if signal == "run":
                # start clock set
                stc = time.perf_counter_ns()

                # get plant output
                _, y0 = tccp.recv()
                _, y1 = tccp.recv()
                y[0, 0] = y0
                y[1, 0] = y1

                # send control input data
                tccp.send(u[0, 0])

                # y and u value encryption after packing
                x_enc, y_enc = enc_4_obs.enc_signal(x, y)
                
                ## controller description ##
                # ------------------------------------------------ #
                # get control input on ciphertext space
                enc_xn, enc_u = obs_enc.get_output(x_enc, y_enc)
                # ------------------------------------------------ #

                dec_x, dec_u = enc_4_obs.dec_signal(enc_xn, enc_u)

                # de-quantization
                for i in range(4):
                    x[i, 0] = float(dec_x[i, 0]) / enc_4_obs.r / enc_4_obs.s 

                u[0, 0] = float(dec_u[0, 0]) / enc_4_obs.r / enc_4_obs.s 
                print(x)

                # end clock set
                edc = time.perf_counter_ns()
                duration = (edc - stc) / 1000000
                print(f"loop time: {duration}ms")

                # ------------------------------------------------ #
            elif signal == "end":
                # end of loop signal get
                run_signal = False
                break

def main():
    obs_encrypted()

if __name__ == "__main__":
    main()

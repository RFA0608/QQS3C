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

def arx_enc():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.025
    run_signal = True

    # get model from model description file
    obs = model.obs(sampling_time)
    arx = model.arx(obs.F, obs.G, obs.H, obs.J)
    arx_q = model.arx_q(arx.HG, arx.HL)

    # set quantized level and quantize matrix
    arx_q.set_level(1000, 1000)
    arx_q.quantize()

    # get crypto model from model_enc
    crypto_cl = model_enc.crypto()
    enc_4_arx = model_enc.enc_for_arx(crypto_cl, arx_q.HG_q, arx_q.HL_q)
    enc_4_arx.set_level(arx_q.r, arx_q.s)
    arx_enc = model_enc.arx_enc(crypto_cl.crypto_context, enc_4_arx.PQ_enc, enc_4_arx.Z_enc)

    # input/output initialization
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
                signal = enc_4_arx.enc_signal(y, u)
                
                ## controller description ##
                # ------------------------------------------------ #
                # ctrl mem update on encrypted space after encryption input/output value
                arx_enc.mem_update(signal)
                
                # get control input on ciphertext space
                enc_u = arx_enc.get_output()
                # ------------------------------------------------ #

                int_u = enc_4_arx.dec_signal(enc_u)

                u[0, 0] = float(int_u) / enc_4_arx.r / enc_4_arx.s

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
    arx_enc()

if __name__ == "__main__":
    main()
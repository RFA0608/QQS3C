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

def fs_encrypted():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.02
    run_signal = True

    # get model from model description file
    obs = model.obs(sampling_time)
    fs = model.fs(obs.H)
    fs_q = model.fs_q(fs.H)
    
    # set quantized level and quantize matrix
    fs_q.set_level(1000, 1000)
    fs_q.quantize()

    # get crypto model from model_enc
    crypto_cl = model_enc.crypto()
    enc_4_fs = model_enc.enc_for_fs(crypto_cl, fs_q.H_q)
    enc_4_fs.set_level(fs_q.r, fs_q.s)
    fs_enc = model_enc.fs_enc(crypto_cl.crypto_context, enc_4_fs.H_enc)

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

                # state estimation on plant and encryption
                obs.state_update(y)
                x_enc = enc_4_fs.enc_signal(obs.x)
                
                ## controller description ##
                # ------------------------------------------------ #
                # get control input on ciphertext space
                enc_u = fs_enc.get_output(x_enc)
                # ------------------------------------------------ #

                int_u = enc_4_fs.dec_signal(enc_u)

                u[0, 0] = float(int_u) / enc_4_fs.r / enc_4_fs.s

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
    fs_encrypted()

if __name__ == "__main__":
    main()

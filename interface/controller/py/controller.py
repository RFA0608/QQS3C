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

def origianl():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.02
    run_signal = True

    # get model from model description file
    ctrl = model.ctrl(sampling_time)

    # input/output initialization
    y = np.array([[0],
                  [0]], dtype=float)
    u = np.array([[0]], dtype=float)

    with tcc.tcp_client(HOST, PORT) as tccp:
        while run_signal:
            # running signal send for controller
            _, signal = tccp.recv()

            if signal == "run":
                # get plant output
                _, y0 = tccp.recv()
                _, y1 = tccp.recv()
                y[0, 0] = y0
                y[1, 0] = y1

                # send control input data
                tccp.send(u[0, 0])

                # plant state update and generate output
                ctrl.state_update(y)
                u = ctrl.get_output()
            elif signal == "end":
                # end of loop signal get
                run_signal = False
                break

def arx():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.02
    run_signal = True

    # get model from model description file
    ctrl = model.ctrl(sampling_time)
    ctrl_arx = model.ctrl_arx(ctrl.F, ctrl.G, ctrl.H, ctrl.J)

    # input/output initialization
    y = np.array([[0],
                  [0]], dtype=float)
    u = np.array([[0]], dtype=float)

    with tcc.tcp_client(HOST, PORT) as tccp:
        while run_signal:
            # running signal send for controller
            _, signal = tccp.recv()

            if signal == "run":
                # get plant output
                _, y0 = tccp.recv()
                _, y1 = tccp.recv()
                y[0, 0] = y0
                y[1, 0] = y1

                # send control input data
                tccp.send(u[0, 0])

                # arx memory update and generate output
                ctrl_arx.mem_update(y, u)
                u = ctrl_arx.get_output()
            elif signal == "end":
                # end of loop signal get
                run_signal = False
                break

def arx_q():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.02
    run_signal = True

    # get model from model description file
    ctrl = model.ctrl(sampling_time)
    ctrl_arx = model.ctrl_arx(ctrl.F, ctrl.G, ctrl.H, ctrl.J)
    ctrl_arx_q = model.ctrl_arx_q(ctrl_arx.HG, ctrl_arx.HL)

    # set quantized level and quantize matrix
    ctrl_arx_q.set_level(1000, 1000)
    ctrl_arx_q.quantize()

    # input/output initialization
    y = np.array([[0],
                  [0]], dtype=float)
    u = np.array([[0]], dtype=float)

    with tcc.tcp_client(HOST, PORT) as tccp:
        while run_signal:
            # running signal send for controller
            _, signal = tccp.recv()

            if signal == "run":
                # get plant output
                _, y0 = tccp.recv()
                _, y1 = tccp.recv()
                y[0, 0] = y0
                y[1, 0] = y1

                # send control input data
                tccp.send(u[0, 0])

                # arx memory update and generate output
                ctrl_arx_q.mem_update(y, u)
                u = ctrl_arx_q.get_output()
            elif signal == "end":
                # end of loop signal get
                run_signal = False
                break

def arx_enc():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.02
    run_signal = True

    # get model from model description file
    ctrl = model.ctrl(sampling_time)
    ctrl_arx = model.ctrl_arx(ctrl.F, ctrl.G, ctrl.H, ctrl.J)
    ctrl_arx_q = model.ctrl_arx_q(ctrl_arx.HG, ctrl_arx.HL)

    # set quantized level and quantize matrix
    ctrl_arx_q.set_level(1000, 1000)
    ctrl_arx_q.quantize()

    # get crypto model from model_enc
    crypto_cl = model_enc.crypto()
    enc_4_sys = model_enc.enc_for_system(crypto_cl, ctrl_arx_q.HG_q, ctrl_arx_q.HL_q)
    enc_4_sys.set_level(ctrl_arx_q.r, ctrl_arx_q.s)
    ctrl_enc = model_enc.ctrl_enc(crypto_cl.crypto_context, enc_4_sys.PQ_enc, enc_4_sys.Z_enc)

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
                signal = enc_4_sys.enc_signal(y, u)
                
                ## controller description ##
                # ------------------------------------------------ #
                # ctrl mem update on encrypted space after encryption input/output value
                ctrl_enc.mem_update(signal)
                
                # get control input on ciphertext space
                enc_u = ctrl_enc.get_output()
                # ------------------------------------------------ #

                int_u = enc_4_sys.dec_signal(enc_u)

                u[0, 0] = float(int_u) / ctrl_arx_q.r / ctrl_arx_q.s

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
    # origianl()
    # arx()
    # arx_q()
    arx_enc()
    
if __name__ == "__main__":
    main()

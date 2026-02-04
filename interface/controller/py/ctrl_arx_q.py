# get tcp_protocol description (vscode[debuger] launched at root directory)
import sys
sys.path.append(r".communication/py")
import tcp_protocol_client as tcc

# init tcp host and port
HOST = 'localhost'
PORT = 9999

# get model description
import model

# get other tools
import numpy as np

def arx_quantized():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.02
    run_signal = True

    # get model from model description file
    obs = model.obs(sampling_time)
    arx = model.arx(obs.F, obs.G, obs.H, obs.J)
    arx_q = model.arx_q(arx.HG, arx.HL)

    # set quantized level and quantize matrix
    arx_q.set_level(1000, 1000)
    arx_q.quantize()

    # print matrix of HG_q and HL_q
    print(arx_q.HG_q)
    print(arx_q.HL_q)

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
                arx_q.mem_update(y, u)
                u = arx_q.get_output()
            elif signal == "end":
                # end of loop signal get
                run_signal = False
                break

def main():
    arx_quantized()

if __name__ == "__main__":
    main()

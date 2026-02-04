# get tcp_protocol description (vscode[debuger] launched at root directory)
import sys
sys.path.append(r"./communication/py")
import tcp_protocol_client as tcc

# init tcp host and port
HOST = 'localhost'
PORT = 9999

# get model description
import model

# get other tools
import numpy as np

def obs_quantized():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.025
    run_signal = True

    # get model from model description file
    obs = model.obs(sampling_time)
    obs_q = model.obs_q(obs.F, obs.G, obs.H)

    # set quantized level and quantize matrix
    obs_q.set_level(1000, 1000)
    obs_q.quantize()

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
                # get plant output
                _, y0 = tccp.recv()
                _, y1 = tccp.recv()
                y[0, 0] = y0
                y[1, 0] = y1

                # send control input data
                tccp.send(u[0, 0])

                # state update and generate output
                x = obs_q.state_update(x, y)
                u = obs_q.get_output()
            elif signal == "end":
                # end of loop signal get
                run_signal = False
                break

def main():
    obs_quantized()

if __name__ == "__main__":
    main()
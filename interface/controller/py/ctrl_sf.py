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

# this method only can be used fast sampling time
def state_filter():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.002
    run_signal = True

    # get model from model description file
    sf = model.sf(sampling_time)

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
                sf.state_update(y)
                u = sf.get_output()
                
            elif signal == "end":
                # end of loop signal get
                run_signal = False
                break

def main():
    state_filter()

if __name__ == "__main__":
    main()
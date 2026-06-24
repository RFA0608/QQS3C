import tcp_protocol_client as tcc

# init tcp host and port
HOST = 'localhost'
PORT = 9999

# get model description
import model

# get other tools

import numpy as np

def nobs():
    # set simulation(this section have to set same with plant)
    sampling_time = 0.01
    run_signal = True

    # get model from model description file
    nobs = model.nobs(sampling_time)
    narx = model.narx(nobs, 10)

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

                # state update and generate output
                narx.mem_update(y, u)
                u = narx.get_output()
                
            elif signal == "end":
                # end of loop signal get
                run_signal = False
                break

def main():
    nobs()

if __name__ == "__main__":
    main()

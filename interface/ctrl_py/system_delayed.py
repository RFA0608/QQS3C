# Need to move from the venv or operational reference position to the Python folder at the bottom
import sys
sys.path.append(r"./py")
sys.path.append(r"../py")
sys.path.append(r"../../py")
sys.path.append(r"../../../py")

import tcp_protocol_client as tcc
import controller as ctr

import time
import os

HOST = 'localhost'
PORT = 9999

def main():
    ts = 20
    margin = 0.25
    state = 1
    y0 = 0.0
    y1 = 0.0
    u = 0.0
    stc = 0.0
    edc = 0.0
    EoL = True
    controller_obj = ctr.Controller()

    with tcc.tcp_client(HOST, PORT) as tccp:
        while EoL:
            if state == 1:
                _, flag = tccp.recv()

                if flag == "R":
                    stc = time.perf_counter_ns() / 1000000

                    tccp.send("ITR")

                    _, y0 = tccp.recv()
                    _, y1 = tccp.recv()
                    tccp.send(u)

                    print(f"y0: {y0} | y1: {y1}")

                    state = 2
                elif flag == "E":
                    EoL = False
                else:
                    os.Exit(-1)
            elif state == 2:
                _, flag = tccp.recv()

                if flag == "R":
                    tccp.send("W")

                    controller_obj.state_update(y0, y1)
                    u = controller_obj.ctrl_input()
                    
                    state = 3
                elif flag == "E":
                    EoL = False
                else:
                    os.Exit(-1)
            elif state == 3:
                while True:
                    _, flag = tccp.recv()
                    
                    if flag == "R":
                        edc = time.perf_counter_ns() / 1000000
                        
                        if (edc - stc) < (ts - margin):
                            tccp.send("W")
                        else:
                            tccp.send("W")
                            print(f"sample_period: {edc - stc}ms")
                            state = 1
                            break
                    elif flag == "E":
                        EoL = False
                        break
                    else:
                        os.Exit(-1)
            else:
                os.Exit(-1)

if __name__ == "__main__":
    main()

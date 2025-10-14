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
    state = 1
    y0 = 0.0
    y1 = 0.0
    u = 0.0
    time_stack = 0
    EoL = True
    controller_obj = ctr.Controller()

    with tcc.tcp_client(HOST, PORT) as tccp:
        while EoL:
            if state == 1:
                _, flag = tccp.recv()

                if flag == "R":
                    tccp.send("ITR")
                    _, y0 = tccp.recv()
                    _, y1 = tccp.recv()
                    tccp.send(u)
                    print(f"y0: {y0} | y1: {y1}")

                    time_stack = time_stack + 1
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

                    time_stack = time_stack + 1
                    state = 3
                elif flag == "E":
                    EoL = False
                else:
                    os.Exit(-1)
            elif state == 3:
                while True:
                    _, flag = tccp.recv()
                    
                    if flag == "R":
                        time_stack = time_stack + 1
                        
                        if time_stack < ts:
                            tccp.send("W")
                        else:
                            tccp.send("W")
                            print(f"sample_period: {time_stack}ms")
                            time_stack = 0
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

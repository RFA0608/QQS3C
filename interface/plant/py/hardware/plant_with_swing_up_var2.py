# get quanser interface lib and tcp_protocol description (vscode[debuger] launched at root directory)
import sys
sys.path.append(r"C:\Quanser\0_libraries\python")
from pal.products.qube import QubeServo2, QubeServo3
from pal.utilities.math import SignalGenerator, ddt_filter
from pal.utilities.scope import Scope

sys.path.append(r"./py")
import tcp_protocol_server as tcs

# init tcp host and port
HOST = '0.0.0.0'
PORT = 9999

# get other tools
from threading import Thread
import signal
import time
import math
import numpy as np

# Thread hanlder initialization
global KILL_THREAD
KILL_THREAD = False
def sig_handler(*args):
    global KILL_THREAD
    KILL_THREAD = True
signal.signal(signal.SIGINT, sig_handler)

# simulation time and plotting set
simulationTime = 30 # will run for 30 seconds
color = np.array([0, 1, 0], dtype=np.float64)

scopePendulum = Scope(
    title='Pendulum encoder - alpha (rad)',
    timeWindow=10,
    xLabel='Time (s)',
    yLabel='Position (rad)')
scopePendulum.attachSignal(name='Pendulum - alpha (rad)',  width=1)

scopeBase = Scope(
    title='Base encoder - theta (rad)',
    timeWindow=10,
    xLabel='Time (s)',
    yLabel='Position (rad)')
scopeBase.attachSignal(name='Base - theta (rad)',  width=1)

scopeVoltage = Scope(
    title='Motor Voltage',
    timeWindow=10,
    xLabel='Time (s)',
    yLabel='Voltage (volts)')
scopeVoltage.attachSignal(name='Voltage',  width=1)

# control-system scenario
def control_loop():
    # interface setting #
    # ------------------------------------------------ #
    # qube version, using hardware, pendulum
    qubeversion = 3
    hardware = 1
    pendulum = 1

    # frequency of system holder and sampler
    frequency = 40 # hz

    # for scope sampling rate
    countMax = frequency / 50
    count = 0

    # class initialization
    QubeClass = QubeServo3

    # swing-up standing gate
    stand_run = False

    # describe #
    # ------------------------------------------------ #
    # instance of hardware model 
    with QubeClass(hardware=hardware, pendulum=pendulum, frequency=frequency) as myQube:
        # instance of tcp layer
        with tcs.tcp_server(HOST, PORT) as tcsp:
            startTime = 0
            timeStamp = 0
            def elapsed_time():
                return time.time() - startTime
            startTime = time.time()

            while timeStamp < simulationTime and not KILL_THREAD:
                if not stand_run:
                    # read sensor information
                    myQube.read_outputs()

                    # calc output
                    theta = myQube.motorPosition * -1
                    alpha_f =  myQube.pendulumPosition
                    alpha = np.mod(alpha_f, 2*np.pi) - np.pi
                    alpha_deg = alpha * 180 / np.pi
                    alpha_f_dot, state_alpha_dot = ddt_filter(alpha_f, state_alpha_dot, 100, 1/frequency)
                    alpha_f_2dot, state_alpha_2dot = ddt_filter(alpha_f_dot, state_alpha_2dot, 100, 1/frequency)

                    # base limitation edge dectection
                    barrier_edge = np.array([0.0, 0.0])
                    barrier_flag = False;
                    barrier_edge[1] = barrier_edge[0]
                    barrier_edge[0] = math.degrees(theta)

                    # edge detect
                    if(barrier_edge[0] >= 10 and barrier_edge[1] < 10):
                        barrier_flag = False
                    elif(barrier_edge[0] < -10 and barrier_edge[1] >= -10):
                        barrier_flag = True

                    # sign(alpha_2dot) swing up
                    if(alpha_f_2dot > 0):
                        if(barrier_flag):
                            voltage = 0
                        else:
                            voltage = 8
                    else:
                        if(not barrier_flag):
                            voltage = 0
                        else:
                            voltage = -8

                    if alpha_deg< 10:
                        voltage = 0
                        stand_run = True
                    
                    # write commands
                    myQube.write_voltage(voltage)

                    print(f"control start: {stand_run}")
                else:
                    # running signal send for controller
                    tcsp.send("run")
    
                    # read sensor information
                    myQube.read_outputs()
    
                    # calc output
                    theta = myQube.motorPosition * -1
                    alpha_f =  myQube.pendulumPosition
                    alpha = np.mod(alpha_f, 2*np.pi) - np.pi
                    alpha_deg = alpha * 180 / np.pi
    
                    # send plant output
                    tcsp.send(-theta)
                    tcsp.send(-alpha)
    
                    # get control input
                    _, u = tcsp.recv()
    
                    # running range set
                    if abs(alpha_deg) < 15:
                        voltage = u
                    else:
                        voltage = 0
    
                    # write commands
                    myQube.write_voltage(voltage)

                # plot to scopes
                count += 1
                if count >= countMax:
                    scopePendulum.sample(timeStamp, [-alpha])
                    scopeBase.sample(timeStamp, [-theta])
                    scopeVoltage.sample(timeStamp,[voltage])
                    count = 0

                timeStamp = elapsed_time()

            tcsp.send("end")

def main():
    thread_cl = Thread(target=control_loop)
    thread_cl.start()

    while thread_cl.is_alive() and (not KILL_THREAD):

        # This must be called regularly or the scope windows will freeze
        # Must be called in the main thread.
        Scope.refreshAll()
        time.sleep(0.01)

    input('Press the enter key to exit.')

if __name__ == "__main__":
    main()

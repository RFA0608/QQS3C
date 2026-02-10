# get quanser interface lib and tcp_protocol description (vscode[debuger] launched at root directory)
import sys
sys.path.append(r"C:\Quanser\0_libraries\python")
from pal.products.qube import QubeServo2, QubeServo3
from pal.utilities.math import SignalGenerator, ddt_filter
from pal.utilities.scope import Scope

sys.path.append(r"./communication/py")
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
    frequency = 50 # hz

    # for scope sampling rate
    countMax = frequency / 50
    count = 0

    # class initialization
    QubeClass = QubeServo3

    # for state estimation
    state_theta_dot = np.array([0,0], dtype=np.float64)
    state_alpha_dot = np.array([0,0], dtype=np.float64)
    state_alpha_f_dot = np.array([0,0], dtype=np.float64)
    state_alpha_f_2dot = np.array([0,0], dtype=np.float64)

    # swing-up standing gate
    stand_run = False
    change_flag = False
    set_time = 0
    switching_time = 1

    # gain of full-state(use initial part of swing-up only 50hz based)
    K = np.array([-2.0, 28.0, -1.5, 2.5])

    # gain P of swing up and bumpping gain R
    P = 0.015
    R = 1

    # switching target angle
    angle = 5

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
                    alpha_deg = abs(math.degrees(alpha))

                    # Calculate angular velocities with filter of 50 and 100 rad
                    theta_dot, state_theta_dot = ddt_filter(theta, state_theta_dot, 50, 1/frequency)
                    alpha_dot, state_alpha_dot = ddt_filter(alpha, state_alpha_dot, 100, 1/frequency)
                    alpha_f_dot, state_alpha_f_dot = ddt_filter(alpha_f, state_alpha_f_dot, 100, 1/frequency)
                    alpha_f_2dot, state_alpha_f_2dot = ddt_filter(alpha_f_dot, state_alpha_f_2dot, 100, 1/frequency)
                    states = np.array([theta, alpha, theta_dot, alpha_dot])

                    # base limitation edge dectection
                    barrier_edge = np.array([0.0, 0.0])
                    barrier_flag = False
                    barrier_edge[1] = barrier_edge[0]
                    barrier_edge[0] = math.degrees(theta)

                    # barrier of base set
                    barrier_edge = np.array([0.0, 0.0])
                    barrier_flag = False
                    barrier_limit = 5

                    if(alpha_deg > angle and (not change_flag)):
                        barrier_edge[1] = barrier_edge[0]
                        barrier_edge[0] = math.degrees(theta)

                        if(barrier_edge[0] >= barrier_limit and barrier_edge[1] < barrier_limit):
                            barrier_flag = False
                        elif(barrier_edge[0] < -barrier_limit and barrier_edge[1] >= -barrier_limit):
                            barrier_flag = True

                        if(alpha_f_2dot > 0):
                            if(barrier_flag):
                                voltage = R
                            else:
                                voltage = P * abs(alpha_deg)
                        else:
                            if(not barrier_flag):
                                voltage = -R
                            else:
                                voltage = -P * abs(alpha_deg)
                    else:
                        voltage = 1*np.dot(K, states)
        
                        if(not change_flag):
                            change_flag = True
                            set_time = timeStamp
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

                    # Calculate angular velocities with filter of 50 and 100 rad
                    theta_dot, state_theta_dot = ddt_filter(theta, state_theta_dot, 50, 1/frequency)
                    alpha_dot, state_alpha_dot = ddt_filter(alpha, state_alpha_dot, 100, 1/frequency)
                    states = np.array([theta, alpha, theta_dot, alpha_dot])
    
                    # send plant output
                    tcsp.send(-theta)
                    tcsp.send(-alpha)
    
                    # get control input
                    _, u = tcsp.recv()
    
                    # swing up trasient responce cushioning
                    if(timeStamp - set_time < switching_time):
                        voltage = 1*np.dot(K, states)
                        print("control object: full-state on plant")
                    else:
                        # running range set
                        if abs(alpha_deg) < 25:
                            voltage = u
                        else:
                            voltage = 0
                        print("control object: outside controller")
                    
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

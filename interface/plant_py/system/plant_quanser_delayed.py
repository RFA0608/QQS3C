import sys
sys.path.append(r"C:\Quanser\0_libraries\python")

from pal.products.qube import QubeServo2, QubeServo3
from pal.utilities.math import SignalGenerator, ddt_filter
from pal.utilities.scope import Scope

# Need to move from the venv or operational reference position to the Python folder at the bottom
sys.path.append(r"./py")
sys.path.append(r"../py")
sys.path.append(r"../../py")
sys.path.append(r"../../../py")

import tcp_protocol_server as tcs

HOST = '0.0.0.0'
PORT = 9999

from threading import Thread
import signal
import time
import math
import numpy as np


global KILL_THREAD
KILL_THREAD = False
def sig_handler(*args):
    global KILL_THREAD
    KILL_THREAD = True
signal.signal(signal.SIGINT, sig_handler)

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

def control_loop():
    qubeVersion = 3

    # Set as 0 if using virtual Qube Servo
    # Set as 1 if using physical Qube Servo
    hardware = 1

    # Only matters when using virtual Qube. 
    # Set as 0 for virtual DC Motor and 1 for virtual pendulum
    # KEEP AS 1, THIS EXAMPLE USES A PENDULUM
    # not important if using virtual
    pendulum = 1

    frequency = 1000# Hz, sampling rate

    # Limit sample rate for scope to 50 hz
    countMax = frequency / 50
    count = 0

    if qubeVersion == 2:
        QubeClass = QubeServo2
    else:
        QubeClass = QubeServo3

    with QubeClass(hardware=hardware, pendulum=pendulum, frequency=frequency) as myQube:
        with tcs.tcp_server(HOST, PORT) as tcsp:
            tcsp.set_metric(False, 100)
            tcsp.set_sampleconst(False, 10)
            tcsp.set_printflag(False)
            u = 0.0

            startTime = 0
            timeStamp = 0
            def elapsed_time():
                return time.time() - startTime
            startTime = time.time()

            while timeStamp < simulationTime and not KILL_THREAD:
                tcsp.send("R")
                _, symb = tcsp.recv()

                # Read sensor information
                myQube.read_outputs()

                theta = myQube.motorPosition * -1
                alpha_f =  myQube.pendulumPosition
                alpha = np.mod(alpha_f, 2*np.pi) - np.pi

                if symb == "ITR":
                    tcsp.send(-theta)
                    tcsp.send(-alpha)
                    _, u = tcsp.recv()

                if abs(u) < 10:
                    voltage = u
                else:
                    voltage = 0

                # # Write commands
                myQube.write_voltage(voltage)

                # Plot to scopes
                count += 1
                if count >= countMax:
                    scopePendulum.sample(timeStamp, [-alpha])
                    scopeBase.sample(timeStamp, [-theta])
                    scopeVoltage.sample(timeStamp,[voltage])
                    count = 0

                timeStamp = elapsed_time()

            tcsp.send("E")

thread = Thread(target=control_loop)
thread.start()

while thread.is_alive() and (not KILL_THREAD):

    # This must be called regularly or the scope windows will freeze
    # Must be called in the main thread.
    Scope.refreshAll()
    time.sleep(0.01)


input('Press the enter key to exit.')

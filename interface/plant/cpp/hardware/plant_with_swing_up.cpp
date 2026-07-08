#define _USE_MATH_DEFINES
#include <iostream>
#include <cstdint>
#include <string>
#include <cmath>
#include <chrono>
#include "tcp_protocol_server_windows.h"
#include "hil.h"
#include "quanser_timer.h"
using namespace std;

const string host = "0.0.0.0";
const int port = 9999;

double ddt_filter(double, vector<double>&, double, double);
void swing_up(vector<double>&, double&);

int main()
{
    t_card board;
    t_error result;
    // if you want to use hardware change to 1 else 0 is virtual(QLab)
    bool hardware = 0;

    if (hardware)
    {
        result = hil_open("qube_servo3_usb", "0", &board);
        if (result < 0)
        {
            cout << "failure to connect hardware" << endl;
            return -1;
        }
    }
    else
    {
        result = hil_open("qube_servo3_usb", "0@tcpip://localhost:18923?nagle='off'", &board);
        if (result < 0)
        {
            cout << "failure to connect QLab" << endl;
            return -1;
        }
    }

    // simulation_time is total run time, sample_time is sample_time.
    int simulation_time = 30;
    double sample_time = 0.02;
    t_timeout interval;
    t_timeout timeout;
    timeout_get_timeout(&interval, sample_time);
    timeout_get_current_time(&timeout);

    // angle[0] = base, angle[1] = pendulum
    double angle[2] = { 0.0, 0.0 };
    double voltage = 0.0;
    int32_t encoder_counts[2];
    uint32_t encoder_channels[2] = { 0, 1 };
    uint32_t analog_channels[2] = { 0 };
    uint32_t digital_channels[1] = { 0 };
    t_boolean digital_values[1] = { 1 };
    hil_write_digital(board, digital_channels, 1, digital_values);

    // swing-up standing gate
    bool stand_run = false;
    bool trans = false;
    double er = 0.2;
    int ei = int(1.0 / sample_time);
    int count = 0;

    // calculation angle
    double theta = 0.0;
    double alpha = 0.0;
    double alpha_deg = 0.0;

    // TCP/IP ready
    tcp_server tcsp = tcp_server(host, port);

    // Just check loop/total time
    auto stc = chrono::high_resolution_clock::now();
    auto edc = chrono::high_resolution_clock::now();
    auto duration = chrono::duration_cast<chrono::nanoseconds>(edc - stc);
    double run_time = duration.count() / 1000000;
    double stack_time = 0.0;

    // For swing-up
    vector<double> state(4);
    vector<double> state_theta_dot = { 0.0, 0.0 };
    vector<double> state_alpha_dot = { 0.0, 0.0 };
    vector<double> K = { -0.87865021, 18.27186509, -0.60044619, 1.53003176 }; // this params have to already known from matlab or python. (based on 20ms)

    // control loop
    for (int64_t i = 0; i < (int64_t)((double)simulation_time / sample_time); i++)
    {
        stc = chrono::high_resolution_clock::now();

        // time sleep
        timeout_add(&timeout, &timeout, &interval);
        qtimer_sleep(&timeout);

        // read sensor
        hil_read_encoder(board, encoder_channels, 2, encoder_counts);
        angle[0] = encoder_counts[0] * (2.0 * M_PI / 2048.0);
        angle[1] = encoder_counts[1] * (2.0 * M_PI / 2048.0);

        // calc output
        theta = -angle[0];
        alpha = fmod(angle[1], 2 * M_PI);
        if (alpha < 0) alpha += 2 * M_PI;
        alpha = alpha - M_PI;
        alpha_deg = alpha * 180 / M_PI;

        state[0] = theta;
        state[1] = alpha;
        state[2] = ddt_filter(theta, state_theta_dot, 50, sample_time);
        state[3] = ddt_filter(alpha, state_alpha_dot, 100, sample_time);

        if (!stand_run && !trans)
        {
            // check output 
            cout << "pendulum angle: " << alpha << endl;
            cout << "base angle: " << theta << endl;

            swing_up(state, voltage);

            if (abs(alpha) < er)
            {
                cout << "ready" << endl;
                trans = true;
            }
        }
        else if (!stand_run && trans)
        {
            voltage = 0.0;
            for (int i = 0; i < 4; i++)
            {
                voltage += K[i] * state[i];
            }

            // saturation
            if (voltage > 15)
            {
                voltage = 15.0;
            }
            else if (voltage < -15)
            {
                voltage = -15.0;
            }
            if (abs(alpha_deg) > 20)
            {
                voltage = 0.0;
            }

            if (count > ei)
            {
                cout << "set" << endl;
                stand_run = true;
            }
            else
            {
                count += 1;
            }
        }
        else
        {
            tcsp.Send<string>("run");

            tcsp.Send<double>(-theta);
            tcsp.Send<double>(-alpha);

            voltage = tcsp.Recv<double>();

            cout << "---------------------------------------------" << endl;
            cout << "pendulum angle: " << alpha << endl;
            cout << "base angle: " << theta << endl;
            cout << "control input: " << voltage << endl;

            // saturation
            if (voltage > 15)
            {
                voltage = 15.0;
            }
            else if (voltage < -15)
            {
                voltage = -15.0;
            }
            if (abs(alpha_deg) > 20)
            {
                voltage = 0.0;
            }
        }

        // actuator write
        hil_write_analog(board, analog_channels, 1, &voltage);

        edc = chrono::high_resolution_clock::now();
        duration = chrono::duration_cast<chrono::nanoseconds>(edc - stc);
        run_time = duration.count() / 1000000;
        stack_time += run_time / 1000;
        cout << "iter: " << i << " | loop time: " << run_time << "ms | total time: " << stack_time << "s" << endl;
    }

    tcsp.Send<string>("end");

    // logic terminate
    voltage = 0.0;
    hil_write_analog(board, analog_channels, 1, &voltage);
    digital_values[0] = 0;
    hil_write_digital(board, digital_channels, 1, digital_values);
    if (board != NULL)
    {
        hil_close(board);
    }

    return 0;
}

double ddt_filter(double u, vector<double>& state, double A, double Ts)
{
    double y = 1.0 / (A * Ts + 2.0) * (2.0 * A * u - 2 * A * state[0] - state[1] * (A * Ts - 2));

    state[0] = u;
    state[1] = y;
   
    return y;
}

void swing_up(vector<double>& state, double& u)
{
    double mp = 0.024;
    double Lp = 0.129;
    double l = Lp / 2;
    double g = 9.81;
    double Jp = mp * pow(Lp, 2) / 3;

    double E_ref = 0.0;
    double mu = 150.0;

    double E_pot = mp * g * l * (cos(state[1]) - 1);
    double E_kin = 0.5 * Jp * pow(state[3], 2);
    double E_total = E_pot + E_kin;
    double E_err = E_ref - E_total;
    
    double term = signbit(state[3] * cos(state[1])) ? -1.0 : 1.0;
    if (abs(state[3]) < 0.05 && abs(cos(state[1])) < 0.1)
    {
        term = 0.0;
    }
    u = -1 * mu * E_err * term;

    if (-state[0] > 0)
    {
        if (u > 0)
        {
            u = 0.0;
        }
    }
    else
    {
        if (u < 0)
        {
            u = 0.0;
        }
    }

    if (u > 8)
    {
        u = 8.0;
    }
    else if (u < -8)
    {
        u = -8.0;
    }
}
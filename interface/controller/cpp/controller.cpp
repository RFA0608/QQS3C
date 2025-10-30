// get tcp_protocol decription
#include "../../../cpp/tcp_protocol_client.h"

// get other tools
#include <iostream>
#include <string>
#include <chrono>
using namespace std;

// get model description
#include "model_enc.h"

// init tcp host and port
const string host = "127.0.0.1";
const int port = 9999;

int main()
{
    // set simulation(this section have to set same with plant)
    double samplint_time = 0.03;
    bool run_signal = true;

    // get crypto model from model_enc.h
    crypto crypto_cl = crypto();
    enc_for_system enc_4_sys = enc_for_system(crypto_cl);
    enc_4_sys.set_level(1000, 1000);
    ctrl_enc ctrl_enc_v = ctrl_enc(crypto_cl.get_crypto(), crypto_cl.get_relinkey(), crypto_cl.get_galoiskeys());
    ctrl_enc_v.set_pq(enc_4_sys.get_PQ_enc());
    ctrl_enc_v.set_io(enc_4_sys.get_Z_enc());

    // set tcp client
    tcp_client tccp = tcp_client(host, port);
    string signal;

    // for check cycle time
    auto stc = chrono::high_resolution_clock::now();
    auto edc = chrono::high_resolution_clock::now();
    auto duration = chrono::duration_cast<chrono::nanoseconds>(edc - stc);
    double run_time;

    // input/output initialization
    vector<double> y(2, 0.0);
    vector<double> u(1, 0.0);
    vector<int64_t> int_u(1, 0LL);

    while(run_signal)
    {
        signal = tccp.Recv<string>();

        if(signal == "run")
        {
            // start clock set
            stc = chrono::high_resolution_clock::now();

            // get plant output
            double y0 = tccp.Recv<double>();
            double y1 = tccp.Recv<double>();
            y[0] = y0;
            y[1] = y1;
            
            // send control input data
            tccp.Send<double>(u[0]);

            // y and u value encryption after packing
            Ciphertext signal = enc_4_sys.enc_signal(y, u);

            // -- controller description -- //
            // ========================================================== //
            // ctrl mem update on encrypted space after encryption input/output value
            ctrl_enc_v.mem_update(signal);

            // get control input on ciphertext space
            Ciphertext enc_u = ctrl_enc_v.get_output();
            // ========================================================== //

            int_u = enc_4_sys.dec_signal(enc_u); 

            u[0] = (double)(int_u[0]) / enc_4_sys.get_level()[0] / enc_4_sys.get_level()[1];

            // end clock set
            edc = chrono::high_resolution_clock::now();
            duration = chrono::duration_cast<chrono::nanoseconds>(edc - stc);
            run_time = duration.count() / 1000000;
            cout << "loop time: " << run_time << "ms" << endl;

        }
        else if(signal == "end")
        {
            // end of loop signal get
            run_signal = false;
            break;
        }
    }

    return 0;
}

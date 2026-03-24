// This code not clearly launchable yet.
#include <iostream>
#include "hil.h"
#include "quanser_timer.h"
using namespace std;

int main() 
{
    t_card board;
    t_error result;
    
    // connection with hardware
    result = hil_open("qube_servo3_usb", "0", &board);
    if (result < 0) 
    {
        cout << "failure to connect hardware << endl;
        return -1;
    }

    double voltage = 0.0;
    int32_t encoder_counts[2];
    uint32_t encoder_channels[2] = {0, 1}; // sensor read [motor(0), pendulum(1)]
    uint32_t analog_channels[2] = {0};     // sensor write [motor(0)] 

    // control loop
    for (int i = 0; i < 1000; i++) {
        // logic wait to saturation sampling time
        // qtimer_sleep(...); 

        // read sensor
        hil_read_encoder(board, encoder_channels, 2, encoder_counts);

        // --- control logic ---
        // transform encoder count to radian
        // control logic
        // voltage = calculation result;
        // -------------------------------

        // actuator write
        hil_write_analog(board, analog_channels, 1, &voltage);
    }

    // logic terminate
    voltage = 0.0;
    hil_write_analog(board, analog_channels, 1, &voltage); // stop motor
    hil_close(board); // connection free

    return 0;
}

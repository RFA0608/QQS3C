clear all;
clc;

%% from python ctrl_intmat, write observer's state matrix below
F = [2.39584424e-01 -7.35929552e-01 6.87969277e-02 -6.29673407e-02;
    1.91780437e-01 -5.93573027e-01 4.84126494e-02 -4.23193298e-02;
    9.60591961e+00 -7.17060353e+01 5.90352651e+00 -6.31747953e+00;
    2.05679325e+01 -7.88962699e+01 4.88319775e+00 -5.26850061e+00];
G = [0.97070195 0.06185157;
     0.01684992  0.94770402;
     11.52542714  3.98037405;
     0.47580911 13.75004665];
H = [18.78737489 -62.91378729 4.35984332 -5.64349325];


%% Converting the state matrix into integers
% One may freely change F, G, and H to different systems as they choose
% Finds R such that (F-RH) is an integer matrix through pole-placement


% Assign integer poles to (F-RH)
poles = [0 1 2 -1]; % Must consist of n-integers!
R = place(F.',H.',poles).';


% Convert to companion canonical form 
sys = ss(F-R*H, G, H, []);
[csys,T] = canon(sys, 'companion');
display(T)




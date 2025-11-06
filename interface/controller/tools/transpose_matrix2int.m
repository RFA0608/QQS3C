clear all;
clc;

%% from python ctrl_intmat, write observer's state matrix below
F = [ 2.30954205e-01 -7.13560963e-01  6.69616419e-02 -6.08793400e-02;
  1.83228262e-01 -5.71358193e-01  4.65918153e-02 -4.02477706e-02;
  8.74186062e+00 -6.94572068e+01  5.71914323e+00 -6.10771361e+00;
  1.97077072e+01 -7.66560638e+01  4.69957841e+00 -5.05960372e+00];
G = [ 0.970755    0.06187669;
  0.01689247  0.94770656;
 11.52775961  3.98127562;
  0.4778784  13.75025036];
H = [ 20.18324641 -68.22150653   4.69924381  -6.111673];


%% Converting the state matrix into integers
% One may freely change F, G, and H to different systems as they choose
% Finds R such that (F-RH) is an integer matrix through pole-placement


% Assign integer poles to (F-RH)
poles = [0 1 2 -1]; % Must consist of n-integers!
R = place(F.',H.',poles).';


% Convert to modal canonical form 
sys = ss(F-R*H, G, H, []);
[csys,T] = canon(sys, 'companion');
display(T)


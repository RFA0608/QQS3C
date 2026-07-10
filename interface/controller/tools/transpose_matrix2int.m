clear all;
clc;

%% from python ctrl_intmat, write observer's state matrix below
F = [-3.10950411e-01 -3.50949933e-01  3.54370756e-02 -2.67039096e-02;
  4.54151518e-02 -8.95791237e-01  1.53155079e-02 -6.34147498e-03;
 -2.04676835e+01 -3.40807411e+01  2.55124745e+00 -2.67342438e+00;
  4.81951566e+00 -6.67790975e+01  1.54481638e+00 -1.63955277e+00];
G = [1.35912206e+00 6.15692722e-02;
 2.37714167e-03 1.63159004e+00;
 2.53083766e+01 5.01270835e+00;
 1.10917234e-03 4.01302382e+01];
H = [4.30374443 -28.54421455   1.3794122   -2.40365098];


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



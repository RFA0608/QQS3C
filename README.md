# Future work
> Full-state feedback encryption, methond of getting full-state: ddt-fillter, observer.
>> 1. if use ddt-fillter we get state x and u = -K(A-BK)x, -K(A-BK) and x encryption.
>> 2. else use observer we get state x+ and u = Hx+, H and x+ encryption.

> Observer based state re-encryption.
>> x+ = Fx+Gy, u = Hx+, All component encryption and x+ and u re-encryption.

# Before useing
All about code have to launch root of file. So please launch debugger(vscode) on root of file.

# Process
## Setting
### WSL
1. WSL launch and download file copy on WSL.
2. On root of file, You write "python3 -m venv venv" on CMD.
3. Continuously write "source ./venv/bin/activate" on same windows.
4. After check running venv enviroment, write "pip install numpy", "pip install matplotlib", "pip install control", "pip install openfhe" on same windows.

5. If you want to use cpp controller file with Microsoft SEAL, you will need install SEAL library. Check "SEAL installation method" file.

### windows
1. Launch powershell and write "ipconfig" on there.
2. Save IPv4 address of vEthernet (WSL (Hyper-V...))

## Implementation
### WSL
#### py
1. On root of file, launch vscode on windows and WSL.
2. Find "controller.py" file on interface/controller/py folder on vscode on WSL.
3. On WSL, change HOST to IPv4 address before we saved.

#### cpp
1. On root of file, launch vscode on windows and WSL.
2. Find "controller.cpp" file on interface/controller/cpp folder on vscode on WSL.
3. On WSL, change HOST to IPv4 address before we saved.
4. Move directory to interface/controller/cpp, write command "cmake ." and "make" by order.
5. You can see a file which name of system_enc. That is Binary object that we should launch for control.

### windows
1. Find "plant.py" file on interface/plant/py folder on vscode on windows.

### Order of operation
#### py
1. Run plant.py file on windows.
2. Run controller.py file on WSL.

#### cpp
1. Run plant.py file on windows.
2. Write command "./system_enc" on the path of interface/controller/cpp.

And pendulum swing-up manualy

# Demonstration Video
https://youtu.be/_wIs1nvavok

"openfhe-python" does not reach 128 lambda bits security. Because there has no margin between sampling period and calculation time related to ring dimension.

On the other hand, "Microsoft SEAL" can control with 25ms sampling time to satisfy 128 lambda bits security.

Recently modified: 251030-0654 (year month day - hour minute)

# Before using
All about code have to launch root of file. So please launch debugger(vscode) on root of file.

# Process for simulation
## Setting
This require WSL enviroment for using openFHE and SEAL library.

### WSL
1. WSL launch and download file copy on WSL.
2. On root of file, You write "python3 -m venv venv" on CMD.
3. Continuously write "source ./venv/bin/activate" on same windows.
4. After check running venv enviroment, write "pip install numpy", "pip install matplotlib", "pip install control", "pip install openfhe" on same windows.

5. If you want to use cpp controller file with Microsoft SEAL, you will need install SEAL library. Check "SEAL installation method" file on git page.

### windows
1. Launch powershell and write "ipconfig" on there.
2. Save IPv4 address of vEthernet (WSL (Hyper-V...))

## Implementation
### WSL
#### py
1. On root of file, launch vscode on windows and WSL.
2. Find controller description code set which are located in interface/controller/py folder on vscode on WSL.
3. Select file which is name like "ctrl_***.py", Instruction what that file mean refer bellow.
   - "ctrl_sf.py": controller made with d/dt filter. That only can use if sampling time faster than 5ms.
   - "ctrl_obs.py": controller made with observer technique.
   - "ctrl_obs_q.py": quantization "ctrl_obs.py"'s controller.
   - "ctrl_obs_enc.py": encryption "ctrl_obs_q.py"'s controller. That doesn't operate as well in this version.
   - "ctrl_fs.py": controller made with observer technique on plant and full state controller decription.
   - "ctrl_fs_q.py": quantization "ctrl_fs.py"'s part of controller.
   - "ctrl_fs_enc.py": encryption "ctrl_fs_q.py"'s part of controller.
   - "ctrl_arx.py": controller made with what is transformed observer to AutoRegressive&eXogenous input model.
   - "ctrl_arx_q.py": quantization "ctrl_arx.py"'s controller.
   - "ctrl_arx_enc.py" encryption "ctrl_arx_q.py"'s controller.
5. On WSL, change HOST to IPv4 address to before we saved in "ctrl_**.py" code.

You can see controller decription(making method) on "model.py" and "model_enc.py"

#### cpp
1. On root of file, launch vscode on windows and WSL.
2. Find "ctrl_arx_enc.cpp" file on interface/controller/cpp folder on vscode on WSL.
3. On WSL, change HOST to IPv4 address to before we saved in the code.
4. Move directory to interface/controller/cpp, write command "cmake ." and "make" by order on CMD.
5. You can see a file which name of "ctrl_arx_enc". That is Binary object that we should launch for control.

### windows
1. Find "plant.py" file on interface/plant/hardware folder on vscode on windows.

If you want to test the control operation, you can use "plant.py" on interface/plant/simulation forder.
That make a result on interface/plant/simulation/result folder which name "plant output as sim.png".

Since it is in the same form as the hardware communication of the Quanser Qube Servo 3, testing it with it can confirm the problem in communication.
(Also plant model is linearlization at equilibrium point)

### Order of operation
#### py
1. Run plant.py file on windows.
2. Run "ctrl_***.py" file on WSL.

#### cpp
1. Run plant.py file on windows.
2. Write command "./ctrl_arx_enc" on the path of interface/controller/cpp.

And pendulum swing-up manualy

# Demonstration Video
https://youtu.be/_wIs1nvavok

"openfhe-python" does not reach 128 lambda bits security. Because there has no margin between sampling period and calculation time related to ring dimension.

On the other hand, "Microsoft SEAL" can control with 25ms sampling time to satisfy 128 lambda bits security.

Recently modified: 251104-1926 (year month day - hour minute) [KST]

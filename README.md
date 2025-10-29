# Modifyed point from scheduled_... branch
this branch's aim is using plant's sampler.

# Before useing
All about code have to launch root of file. So please launch debugger(vscode) on root of file.

# Process
## Setting
### WSL
1. WSL launch and download file copy on WSL.
2. On root of file, You write "python3 -m venv venv" on CMD.
3. Continuously write "source ./venv/bin/activate" on same window.
4. After check running venv enviroment, write "pip install numpy", "pip install matplotlib", "pip install control", "pip install openfhe" on same window.

### Windows
1. Launch powershell and write "ipconfig" on there.
2. Save IPv4 address of vEthernet (WSL (Hyper-V...))

## Implementation
### WSL
1. On root of file, launch vscode on window and WSL.
2. Find "controller.py" file on interface/controller/py folder on vscode on WSL.
3. On WSL, change HOST to IPv4 address before we saved.

### Windows
1. Find "plant.py" file on interface/plant/py folder on vscode on window.

### Order of operation
1. Run plant.py file on window
2. Run controller.py file on WSL

And pendulum swing-up manualy

# Demonstration Video
https://youtu.be/_wIs1nvavok

Recently modified: 251030-0158 (year month day - hour minute)

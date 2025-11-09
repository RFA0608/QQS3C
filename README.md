# QQS3C
QQS3C provides the drive code for cryptographic control for the Quanser Qube Servo 3 model. 
The code transforms dynamic controllers through various methods and then drives the system through computationally homomorphic cryptography. 
The cryptographic libraries for computational homomorphism use [Microsoft SEAL](https://github.com/microsoft/SEAL), [OpenFHE-python](https://github.com/openfheorg/openfhe-python), and [CDSL-EncryptedControl](https://github.com/CDSL-EncryptedControl/CDSL/tree/main) using [lattigo](https://github.com/tuneinsight/lattigo).
The encryption control technique uses the one implemented in [SNU](https://post.cdsl.kr/) and [SEOULTECH](http://cdslst.kr)'s CDSL.
The code uses Quanser's Qube Servo 3 model [Qube Servo 3](https://github.com/quanser/Quanser_Academic_Resources/tree/dev-windows) python API.

---

## Implementation Direction
The code was implemented through data communication with the Quanser API via TCP/IP in order to use Microsoft' SEAL, a C-style homomorphic cryptographic library that can be operated, lattigo (CDSL) written in GO, and OpenFHE-pytho that can be run in a Linux environment, since the hardware API provided by Quanser is only Python and runs in a Windows environment.

---

## Features
The code implements a python version controller, a cpp version controller, and a go version controller.
The interfacing code of the python simulator and the actual device matching the controller can be found in "interface/plant" respectively.
The actual device consists of a single file, "plant.py" in "interface/plant/py/hardware", while the simulator consists of "model.py" and "plant.py" in "interface/plant/py/simulation".
**Code explanation and technical interpretation can be found at the link below.**
**[QQS3C](https://publish.obsidian.md/qqs3c)**


### python version controller
You can check the "ctrl_*.py" controller file, which is written in python, in the "interface/controller/py" folder of the code.
They are implemented in four technically different forms.

1. ctrl_sf.py
   >> Using d/dt filter from Quanser Qube Servo 3. 
2. ctrl_fs.py
3. ctrl_obs.py
4. ctrl_arx.py



# 0️⃣ Before using
All about code have to launch root of file. So please launch debugger(vscode) on root of file. If you download this git file to use "git clone", you can find folder name "QQS3C". Enter that, and write "code ." on CMD. That folder is root folder.

This library require 
1. go version 1.25.1 after
2. c++13 compiler after
3. 3.12.3 python after
at least. 

Ubuntu 24.04 LTS is proper version of WSL as os.

# 1️⃣ Process for simulation
## Setting
This require WSL enviroment for using openFHE and SEAL library.

### WSL
1. WSL launch and download file copy on WSL.
2. On root of file, You write "python3 -m venv venv" on CMD.
3. Continuously write "source ./venv/bin/activate" on same windows.
4. After check running venv enviroment, write "pip install numpy", "pip install matplotlib", "pip install control", "pip install openfhe" on same windows.

5. If you want to use cpp controller file with Microsoft SEAL, you will need install SEAL library. Check "SEAL installation method" file on this git page.

### windows
1. Launch powershell and write "ipconfig" on there.
2. Save IPv4 address of vEthernet (WSL (Hyper-V...))

## Implementation
### WSL
#### py
1. On root of file, launch vscode on windows and WSL.
2. Find controller description code set which are located in interface/controller/py folder on vscode on WSL.
3. Select file which is name like "ctrl_***.py", The instruction of what that means is below.
   - "ctrl_sf.py": controller made with d/dt filter. That only can use if sampling time faster than 5ms.
   - "ctrl_obs.py": controller made with observer technique.
   - "ctrl_obs_q.py": quantization "ctrl_obs.py"'s controller.
   - "ctrl_obs_enc.py": encryption "ctrl_obs_q.py"'s controller. That doesn't operate as well in this version.
   - "ctrl_fs.py": controller made with observer technique on plant and full state controller decription.
   - "ctrl_fs_q.py": quantization "ctrl_fs.py"'s part of controller.
   - "ctrl_fs_enc.py": encryption "ctrl_fs_q.py"'s part of controller.
   - "ctrl_arx.py": controller made with what is transformed observer to AutoRegressive&eXogenous input model.
   - "ctrl_arx_q.py": quantization "ctrl_arx.py"'s controller.
   - "ctrl_arx_enc.py": encryption "ctrl_arx_q.py"'s controller.
   - "ctrl_intmat.py": controller state matrix, which is maded from observer technique, transpose to integer matrix.
        > You can get transformed matrix from MATLAB script file of name "transpose_matrix2int.m" in interface/controller/tools folder.
   - "ctrl_intmat_q.py": quantization "ctrl_intmat.py"'s controller.
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

And pendulum swing-up manualy. 
If you set pendulum to origin(equilibrium) maunualy, controller automatically operate.  

# 3️⃣ Demonstration Video
https://youtu.be/kVwAEByurqQ?si=HSzjDU9NrPQbe-Wl

"openfhe-python" does not reach 128 lambda bits security. Because there has no margin between sampling period and calculation time related to ring dimension / moduli.

On the other hand, "Microsoft SEAL" can control with 20ms sampling time to satisfy 128 lambda bits security.

Recently modified: 251107-1706 (year month day - hour minute) [KST]

# ⚠️
This paper doesn't accurately account for the code. Ready to renewally update Readme and technical resources untill 251113

# Licenses & Acknowledgements

This project utilizes code from several open-source projects. We express our gratitude to their developers. The licenses for these dependencies are listed below.

* **Lattigo (v6)**
    * Licensed under the [Apache License 2.0](https://github.com/tuneinsight/lattigo/blob/main/LICENSE)

* **Microsoft SEAL**
    * Licensed under the [MIT License](https://github.com/microsoft/SEAL/blob/main/LICENSE)

* **CDSL-EncryptedControl**
    * Licensed under the [MIT License](https://github.com/CDSL-EncryptedControl/CDSL/blob/main/LICENSE)

* **OpenFHE (Python)**
    * Licensed under the [BSD 2-Clause License](https://github.com/openfheorg/openfhe-python/blob/main/LICENSE)

* **Numpy**
    * Licensed under the [BSD 3-Clause License](https://github.com/numpy/numpy/blob/main/LICENSE.txt)

* **Matplotlib**
    * Licensed under the [PSF-style License](https://github.com/matplotlib/matplotlib/blob/main/LICENSE/LICENSE)

* **Python Control Systems Library (python-control)**
    * Licensed under the [BSD 3-Clause License](https://github.com/python-control/python-control/blob/main/LICENSE)

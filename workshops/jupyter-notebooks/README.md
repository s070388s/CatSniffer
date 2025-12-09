# Installation

These instructions are exclusively for the installation and configuration of the essential tools required to execute the workshops contained within this folder, which consist of Jupyter notebook files. At this time, these procedures are specifically designed for setup and operation within the Windows operating system.

## Install Python 3.13.3

For windows is necessary to download and install the correct python version, on the following [link](https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe) you can get the installer file, then execute it starting the python installation.

**Note:** For not having problems with the environment paths of windows, mark the option ```Add python.exe to PATH```.

<div align="center">
  <img src="static\python_installation_remark.png" width="400">
</div>

## COPY into the `C:` to avoid issues with the path
Move this folder ```jupyter-notebooks``` to the ```C:\``` location to avoid any issue with some libraries after their installation.

## Setting Up 

### With Virtual Environment (Optional)
To make sure our workshops run smoothly and nothing breaks on your computer, you can setup an isolated space for the project called Virtual Environment.

1. Create the Virtual Environment: This command creates a new folder named venv with everything needed.
```bash
python -m venv venv
```
2. Activate the Environment: Execute this command to use the isolated environment's Python interpreter.

```bash
 .\venv\Scripts\activate
```

### Installing the libraries

Once your Python environment is active (or if you have chosen to install globally), the final step is to install the main tools you will use to open and work with the notebooks.

1. **Install JupyterLab:** This is the core interactive development environment we will use to open, edit, and run the .ipynb files (the notebooks).
```bash
pip install jupyterlab
```
>Important: The installation of jupyterlab might take a few minutes as it downloads several related packages.

2. **Install ipywidgets:** This library is essential for adding interactive elements like sliders or buttons directly into the Jupyter notebooks. It is crucial for certain demonstrations to function correctly.
```bash
pip install ipywidgets
```
## Run Jupyter Lab

Now that all required libraries are successfully installed, you are ready to launch the JupyterLab environment and access the workshop files.

### Launch Command
Run the following command in your terminal while you are still in the root project folder (where your notebooks are located):
```bash
jupyter lab
```
> Note: if a typing_extensions error occurs at the installation, use this command: pip install --upgrade typing_extensions and run `jupyter lab` again

### What Happens Next?
**Automatic Opening:** This command will start a local web server and automatically open your default web browser (like Chrome or Firefox) to the JupyterLab interface.

**File Access:** You will see a list of all files and folders located where you ran the command. From here, simply click on any .ipynb file to open a notebook and begin your work.

**Active Server:** The terminal window where you executed the command will remain open and display server activity. Do not close it while you are using JupyterLab. To stop the server when you are finished, return to the terminal and press Ctrl + C.

## Walk-Through 
The files to execute step by step are the next:

1. **CatSniffer-Minino.ipynb:** This file works to setup and download all tools for Catsniffer board and Minino Board
2. **CatSniffer-Lab1-Meshtastic.ipynb:** The first laboratory to work with Catsniffer and Meshtastic  
3. **CatSniffer-Lab2-Zigbee.ipynb:** The second laboratory to work with Catsniffer and Zigbee Protocol  
4. **CatSniffer-Lab3-BLE.ipynb:** The third laboratory to work with Catsniffer and Minino with the BLE Protocol
5. **Minino - Lab4 - Wifi Captive Portal.ipynb:** The fourth laboratory to work with Minino using the Captive portal Application  
6. **Minino - Lab5 - Wifi Deauthentication.ipynb:** The fifth laboratory to work with Minino and the Wifi Deauthentication   

## Other requirements
For the the Labs 1 and 2 install **Wireshark v4.4**, where you need to install the dissectors for the operative system from here https://github.com/ElectronicCats/CatSniffer-Wireshark/releases/tag/v0.1.1.

### Setup Dissectors
1. Download the dissector for the operative system you’re using from this link https://github.com/ElectronicCats/CatSniffer-Wireshark/releases/tag/v0.1.1
2. Unzip the downloaded file
3. Open Wireshark and navigate “Help > About Wireshark” option
4. Select the Folders tab
5. In the Name column, find the **Personal Plugins** and double click in the path of the Location column
6. Copy the two files (catsniffer_rpi and catsniffersx1262) into the folder **epan**.
7. Open the navigate to Edit and enter to **Preferences** menu, in the Protocols tree, find the “DLT_USER” and select it
8. Click in the “Edit…” button
9. Add the following records:
   - catsniffer_rpi:
     - **DLT**: DLT=147
     - **Payload dissector**: catsniffer_rpi
   - catsniffersx1262_rpi:
     - **DLT**: DLT=148
     - **Payload dissector**: catsniffersx1262_rpi

import os
import subprocess
import threading
import serial.tools.list_ports
import ipywidgets as widgets
from IPython.display import display, clear_output

def run_process_cmd(cmd=[]):
    process =  subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    buffer = ""
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        if line:
            try:
                decoded = line.decode("utf-8", errors="replace")
            except:
                decoded = str(line)
            buffer += decoded
            clear_output(wait=True)
            print(buffer)

def detect_serial_ports(_):
    available_ports = []

    ports = serial.tools.list_ports.comports()
    for port in ports:
        if any(x in port.device for x in ["ttyUSB", "ttyACM", "cu.usbmodem", "usbserial", "COM"]):
            available_ports.append(port.device)

    return available_ports
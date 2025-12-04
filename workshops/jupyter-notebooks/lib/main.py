import os
import time
import queue
import signal
import base64
import subprocess
import threading
import platform
import serial.tools.list_ports
import ipywidgets as widgets
from pathlib import Path
from IPython.display import display, clear_output
from meshtasticLiveDecoder import Monitor, CHANNELS_PRESET, SYNC_WORLD, DEFAULT_KEYS, extract_frame, extract_fields, decrypt, decode_protobuf, print_packet_info

ROOT_PATH       = os.getcwd()
CS_DIRNAME      = "CatSniffer-Tools"
CS_TOOLS_URL    = "https://github.com/ElectronicCats/CatSniffer-Tools.git"
CS_TOOLS_PATH   = os.path.join(ROOT_PATH, CS_DIRNAME)
REQUIREMENTS    = os.path.join(ROOT_PATH, "requirements.txt")
CATSNIFFER_PATH = os.path.join(ROOT_PATH, CS_TOOLS_PATH, "catsniffer")
CATNIP_PATH     = os.path.join(ROOT_PATH, CS_TOOLS_PATH, "catnip_uploader")
PYCATSNIFF_PATH = os.path.join(ROOT_PATH, CS_TOOLS_PATH, "pycatsniffer_bv3")
SXTOOLS_PATH    = os.path.join(ROOT_PATH, CS_TOOLS_PATH, "sx1262Tools")

FREQUENCY_BASE  = str(906.875)
BANDWIDTH_INDEX = str(8)
MESH_DECODER_PRESETS = ["defcon33", "ShortTurbo", "ShortSlow", "ShortFast", "MediumSlow", "MediumFast", "LongSlow", "LongFast", "LongMod", "VLongSlow",
]

WS_WINDOWS_PATH = "C:\\Program Files\\Wireshark\\Wireshark.exe"
WS_LINUX_PATH   = "/usr/bin/wireshark"
WS_MACOS_PATH   = "/Applications/Wireshark.app/Contents/MacOS/Wireshark"

def validate_python_call():
    try:
        output = subprocess.check_output(
            ["python", "--version"], stderr=subprocess.STDOUT
        )
        output = output.decode("utf-8").strip()
        if output.startswith("Python 3."):
            return "python"
    except Exception:
        pass
    try:
        output = subprocess.check_output(
            ["python3", "--version"], stderr=subprocess.STDOUT
        )
        output = output.decode("utf-8").strip()
        if output.startswith("Python 3."):
            return "python3"
    except Exception:
        return None

PYTHON_ENV      = validate_python_call()

def running_windows():
    if platform.system() == "Windows":
        return True
    return False

class Notebook:
    def __init__(self):
        pass
    
    def run_process_cmd(self, cmd=[], print_stdout=True, output_block=None) -> str:
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
                if print_stdout:
                    print(buffer)
                if output_block:
                    output_block.append_stdout(buffer)
        return buffer

    def detect_serial_ports(self, _):
        available_ports = []

        ports = serial.tools.list_ports.comports()
        for port in ports:
            if any(x in port.device for x in ["ttyUSB", "ttyACM", "cu.usbmodem", "usbserial", "COM"]):
                available_ports.append(port.device)

        return available_ports
    
    def clone_catsniffer_tools(self):
        if not os.path.exists(CS_TOOLS_PATH):
            print(f"Cloning repository {CS_TOOLS_URL}...")
            _ = self.run_process_cmd(["git", "clone", CS_TOOLS_URL])
            _ = self.run_process_cmd(["git", "-C", CS_TOOLS_PATH, "checkout", "uf2"])
            _ = self.run_process_cmd(["git", "-C", CS_TOOLS_PATH, "pull"])
            print("Done")
        else:
            print(f"Updating existing repository in {CS_TOOLS_PATH}...")
            try:
                _ = self.run_process_cmd(["git", "-C", CS_TOOLS_PATH, "fetch"])
                _ = self.run_process_cmd(["git", "-C", CS_TOOLS_PATH, "pull"])
            except subprocess.CalledProcessError as e:
                print(f"Failed to update repository: {e}")
    
    def install_catsniffer_requirements(self):
        # Sanity check
        if not os.path.exists(REQUIREMENTS):
            print("Please, contact with the trainers.")
        else:
            print("Installing the requirements...")
            _ = self.run_process_cmd(["pip", "install", "-r", REQUIREMENTS])
            _ = self.run_process_cmd(["pip", "install", CATSNIFFER_PATH])
            print("Done!")
    
    def download_catsniffer_firmware(self):
        cmd = [PYTHON_ENV, os.path.join(CATNIP_PATH, "catnip_uploader.py"), "releases"]
        # Sanity check
        if not os.path.exists(CATNIP_PATH):
            print("Please, run the first code block.")
        else:
            print("Downloading the firmware...")
            _ = self.run_process_cmd(cmd)
    
    # Sanity check
    def get_release_folder(self):
        dir_files = os.listdir(CATNIP_PATH)
        for dirf in dir_files:
            if dirf.startswith("releases_"):
                return dirf
        return None
    
    def flash_uf2_firmware(self, firmware):
        release_path = self.get_release_folder()
        if release_path is None:
            print("Error getting releases folder, please check the requirements blocks")
        else:
            uf2_file = os.path.join(CATNIP_PATH, release_path, firmware)
            file_path = Path(uf2_file)
            while True:
                cmd = [
                    "powershell",
                    "-Command",
                    "(Get-WmiObject Win32_Volume | Where-Object { $_.Label -match 'RPI-RP2' }).DriveLetter"
                ]
                drive = subprocess.run(cmd, capture_output=True, text=True).stdout.strip()
                if drive:
                    print(f"Board detected ({drive}). Flashing firmware...")
                    cmd = [
                        "powershell",
                        "-Command",
                        f"""
                        $drive = (Get-WmiObject Win32_Volume | Where-Object {{ $_.Label -match 'RPI-RP2' }}).DriveLetter
                        if ($drive) {{
                            Copy-Item "{file_path.resolve()}" "$drive\\"
                            Write-Host "File flashed to $drive"
                        }} else {{
                            Write-Host "RP2040 not found"
                        }}
                        """
                    ]
                    
                    print(subprocess.run(cmd, capture_output=True, text=True).stdout)
                    break
                print("Waiting connection RP2040...")
                time.sleep(2)
    
    def flash_cc_fiwmare(self, firmware):
        cmd = [PYTHON_ENV, os.path.join(CATNIP_PATH, "catnip_uploader.py"), "load", firmware, "--validate"]
        print(f"> {' '.join(cmd)}\n")
        self.run_process_cmd(cmd)
                
class SerialConnection:
    def __init__(self):
        self.port = ""
        self.serial_conn = None
    
    def connect(self, port:str = "", baudrate:int = 115200, timeout:int = 1) -> bool:
        try:
            self.serial_conn = serial.Serial(port=port, baudrate=baudrate, timeout=timeout)
            return True
        except Exception as e:
            print(e)
            return False

    def write(self, data) -> None:
        self.serial_conn.write(data)
    
    def disconnect(self) -> None:
        if self.serial_conn:
            self.serial_conn.close()
            self.serial_conn = None
    
    def send_command_string(self, command:str) -> None:
        """Send commmand in string. This function add Carriage return"""
        if self.serial_conn and self.serial_conn.is_open:
            cmd = command + "\r\n"
            self.serial_conn.write(cmd.encode())
    
    def send_command_string_with_response(self, command:str) -> bytes:
        self.send_command_string(command=command)
        time.sleep(0.3)
        try:
            return self.serial_conn.read_all().decode(errors="ignore")
        except:
            return "Nan"
                
class HandsOn1CatsnifferUI:
    def __init__(self):
        self.nb = Notebook()
        self.ser = SerialConnection()
        # ======= UI Terminal ========
        self.output_terminal   = widgets.Output(layout=widgets.Layout(width='100%', height='500px', border="1px solid black", overflow='scroll'))
        self.btn_port          = widgets.Button(description="Scan ports")
        self.input_user        = widgets.Text(placeholder="Type the command", layout=widgets.Layout(width='25%'))
        self.text_frequency   = widgets.Text(value=FREQUENCY_BASE, placeholder="Frequency value", description="Frequency", layout=widgets.Layout(width='25%'))
        self.drop_bandwidth   = widgets.Dropdown(options=["1", "2", "3", "4", "5", "6", "7", "8", "9"], value=BANDWIDTH_INDEX, description='Bandwidth Index:', disabled=False, layout=widgets.Layout(width='25%'))
        self.drop_s_factor   = widgets.Dropdown(options=["6", "7", "8", "9", "10", "11", "12"], value="11", description='Spreading Factor:', disabled=False, layout=widgets.Layout(width='25%'))
        self.text_preamble_l   = widgets.Text(value="8", placeholder="Preamble Length", description="Preamble Length", layout=widgets.Layout(width='25%'))
        self.text_sync_word   = widgets.Text(value="0x2B", placeholder="Sync Word", description="Sync Word", layout=widgets.Layout(width='25%'))
        self.btn_send_command  = widgets.Button(description="Send", icon="arrow-right")
        self.btn_clear_output  = widgets.Button(description="Clear console", icon="eraser")
        self.btn_loop_read     = widgets.Button(description="Open", icon="play-circle", button_style="success")
        self.dropdown_ports    = widgets.Dropdown(options=self.nb.detect_serial_ports(None), description='Ports:', layout=widgets.Layout(width='40%'))
        self.dropdown_baudrate = widgets.Dropdown(options=[9600, 19200, 115200, 921600 ], value=921600, description='Baudrate:', layout=widgets.Layout(width='40%'))
        
        self.loop_thread = threading.Thread()
        self.loop_reading = False
        
        self.btn_port.on_click(self._on_scan_port)
        self.btn_send_command.on_click(self._on_send_command)
        self.btn_clear_output.on_click(self._on_clear_output)
        self.btn_loop_read.on_click(self._on_loop_reading)
        self._on_scan_port(None)
        
        # ======= UI Wireshark ========
        self.output_wireshark = widgets.Output(layout=widgets.Layout(width='100%', height='200px', border="1px solid black", overflow='scroll'))
        self.btn_run_pycat    = widgets.Button(description="Run", icon="play-circle", button_style="success")
        self.btn_stop_pycat   = widgets.Button(description="Stop", icon="stop-circle", button_style="danger")
        
        self.wireshark_thread = threading.Thread()
        self.wireshark_process = None
        
        self.btn_run_pycat.on_click(self._on_run_ws)
        self.btn_stop_pycat.on_click(self._on_stop_ws)
        
        # ======= UI Static Telemetry Decoder ========
        self.output_decoded_tm = widgets.Output(layout=widgets.Layout(width='100%', height='500px', border="1px solid black", overflow='scroll'))
        self.text_payload   = widgets.Text(value="", placeholder="PAYLOAD", description="Payload", layout=widgets.Layout(width='45%'))
        self.text_ext_key   = widgets.Text(value="", placeholder="EXTRACTED KEY", description="Extracted Key", layout=widgets.Layout(width='45%'))
        self.btn_decode    = widgets.Button(description="Decode", icon="key", button_style="primary")
        
        self.btn_decode.on_click(self._on_decode_telemetry)
        
        # ======= UI Live Telemetry Decoder ========
        self.output_live_decoder      = widgets.Output(layout=widgets.Layout(width='100%', height='500px', border="1px solid black", overflow='scroll'))
        self.text_frequency_decoder   = widgets.Text(value=self.text_frequency.value if self.text_frequency.value != "" else FREQUENCY_BASE, placeholder="Frequency value", description="Frequency", layout=widgets.Layout(width='25%'))
        self.dropdown_preset_decoder  = widgets.Dropdown(options=MESH_DECODER_PRESETS, value="LongFast", description='Preset:', layout=widgets.Layout(width='40%'))
        self.btn_run_decode           = widgets.Button(description="Run", icon="key", button_style="success")
        self.btn_stop_decode           = widgets.Button(description="Stop", icon="stop-circle", button_style="danger")
        self.btn_clear_decoder_output = widgets.Button(description="Clear console", icon="eraser")
        
        self.decoder_thread = threading.Thread()
        self.decoder_process = False
        
        self.btn_run_decode.on_click(self._on_run_live_decoding)
        self.btn_stop_decode.on_click(self._on_stop_decoder)
        self.btn_clear_decoder_output.on_click(self._on_clear_decoder_output)
    
    def _loop_reading_worker(self):
        if self.ser.connect(port=self.dropdown_ports.value, baudrate=self.dropdown_baudrate.value):
            self.configure_lora_catsniffer()
            while self.loop_reading:
                data = self.ser.serial_conn.readline()
                if data:
                    self._show_prompt_catsniffer(data.decode("utf-8", errors="ignore"))
                time.sleep(0.1)
            self.ser.disconnect()
            self._show_prompt_user(f"{self.dropdown_ports.value} Closed")
    
    def _show_prompt_catsniffer(self, data):
        prompt = f"[CATSNIFFER] {data}"
        self.output_terminal.append_stdout(prompt)
    
    def _show_prompt_user(self, data):
        prompt = f"> {data}\n"
        self.output_terminal.append_stdout(prompt)
    
    def _on_scan_port(self, _):
        self.dropdown_ports.options = self.nb.detect_serial_ports(None)
    
    def _on_send_command(self, _):
        cmd = self.input_user.value
        self.ser.send_command_string(cmd)
        self.input_user.value = ""

    def _on_clear_output(self, _):
        self.output_terminal.clear_output()
    
    def _on_loop_reading(self, _):
        self.loop_reading = not self.loop_reading
        
        if self.loop_reading:
            if not self.loop_thread.is_alive():
                self.loop_thread = threading.Thread(target=self._loop_reading_worker)
                self.loop_thread.start()
                self.btn_loop_read.description = "Close"
                self.btn_loop_read.icon="stop-circle"
                self.btn_loop_read.button_style='danger'
        else:
            self.btn_loop_read.description = "Open"
            self.btn_loop_read.icon="play-circle"
            self.btn_loop_read.button_style='success'
    
    def _ws_worker(self):
        try:
            cmd = [PYTHON_ENV, os.path.join(PYCATSNIFF_PATH, "cat_sniffer.py"), "lora", "--frequency", str(self.text_frequency.value), "-bw", str(self.drop_bandwidth.value), "-sf", str(self.drop_s_factor.value), "-sw", str(self.text_sync_word.value), "-ff", "-ws", "-st", self.dropdown_ports.value]
            self.output_wireshark.append_stdout(f"> {' '.join(cmd)}\n")
            subprocess.run(cmd)
        except Exception as e:
            print(e)
            self.output_wireshark.append_stdout(e)
    
    def _on_run_ws(self, _):
        self.wireshark_thread = threading.Thread(target=self._ws_worker, daemon=True)
        self.wireshark_thread.start()

    def _on_stop_ws(self, _):
        if self.wireshark_thread and self.wireshark_thread.is_alive():
            try:
                self.wireshark_thread.join(timeout=1)
            except Exception as e:
                print(e)
    
    def _on_decode_telemetry(self, _):
        payload = self.text_payload.value
        key = self.text_ext_key.value
        if payload == "":
            self.output_decoded_tm.append_stdout("ERROR. Please write the command!\n")
            return
        cmd = [PYTHON_ENV, os.path.join(SXTOOLS_PATH, "meshtasticDecoder.py"), "-k", key, "-i", payload]
        self.output_decoded_tm.append_stdout(f"> {' '.join(cmd)}\n")
        ret = self.nb.run_process_cmd(cmd=cmd, print_stdout=False)
        self.output_decoded_tm.append_stdout(ret)
    
    def _on_clear_decoder_output(self, _):
        self.output_live_decoder.clear_output()
    
    def _decoder_worker(self):
        cmd = [PYTHON_ENV, os.path.join(SXTOOLS_PATH, "meshtasticLiveDecoder.py"), "-p", self.dropdown_ports.value, "-baud", str(self.dropdown_baudrate.value), "-f", str(self.text_frequency_decoder.value), "-ps", self.dropdown_preset_decoder.value]
        self.output_live_decoder.append_stdout(f"> {' '.join(cmd)}\n")
        rx_queue = queue.Queue()
        mon = Monitor(self.dropdown_ports.value, self.dropdown_baudrate.value, rx_queue)
        mon.start()
        
        mon.transmit(f"set_bw {CHANNELS_PRESET[self.dropdown_preset_decoder.value]['bw']}")
        mon.transmit(f"set_sf {CHANNELS_PRESET[self.dropdown_preset_decoder.value]['sf']}")
        mon.transmit(f"set_cr {CHANNELS_PRESET[self.dropdown_preset_decoder.value]['cr']}")
        mon.transmit(f"set_pl {CHANNELS_PRESET[self.dropdown_preset_decoder.value]['pl']}")
        mon.transmit(f"set_sw {SYNC_WORLD}")
        mon.transmit(f"set_freq {self.text_frequency_decoder.value}")
        mon.transmit("set_rx")
        try:
            while self.decoder_process:
                if not rx_queue.empty():
                    frame = rx_queue.get()
                    try:
                        raw = extract_frame(frame)
                        fields = extract_fields(raw)
                        for key_b64 in DEFAULT_KEYS:
                            key = base64.b64decode(key_b64)
                            try:
                                decrypted = decrypt(fields['payload'], key, fields['sender'], fields['packet_id'])
                                decoded = decode_protobuf(decrypted, fields['sender'].hex(), fields['dest'].hex())
                                if decoded:
                                    print_packet_info(fields, decrypted, self.output_live_decoder)
                                    self.output_live_decoder.append_stdout(f"[INFO] Successfully decrypted using key: {key_b64}")
                                    self.output_live_decoder.append_stdout(decoded)
                                    break
                            except Exception:
                                continue
                    except Exception as e:
                        self.output_live_decoder.append_stdout(f"[MSG] raw: {frame}\n")
            self.output_live_decoder.append_stdout("\n[INFO] Shutting down gracefully...")
            mon.stop()
        except Exception as e:
            self.output_live_decoder.append_stdout(f"\n[ERROR] {e}")
            mon.stop()

    def _on_run_live_decoding(self, _):
        self.decoder_process = True
        self.decoder_thread = threading.Thread(target=self._decoder_worker, daemon=True)
        self.decoder_thread.start()

    def _on_stop_decoder(self, _):
        if self.decoder_thread and self.decoder_thread.is_alive():
            self.decoder_process = False
            self.decoder_thread.join(timeout=1)
    
    def configure_lora_catsniffer(self):
        self.ser.write(bytes(f"set_freq {self.text_frequency.value}\r\n", "utf-8"))
        self.ser.write(bytes(f"set_bw {str(self.drop_bandwidth.value)}\r\n", "utf-8"))
        self.ser.write(bytes(f"set_sf {str(self.drop_s_factor.value)}\r\n", "utf-8"))
        self.ser.write(bytes(f"set_pl {self.text_preamble_l.value}\r\n", "utf-8"))
        self.ser.write(bytes(f"set_sw {self.text_sync_word.value}\r\n", "utf-8"))
        self.ser.write(b"get_config\r\n")
        self.ser.write(b"set_rx\r\n")
    
    def display_ui_terminal(self):
        display(widgets.VBox([
            widgets.Box([self.btn_port, self.dropdown_ports, self.dropdown_baudrate, self.btn_loop_read]),
            widgets.HBox([self.text_frequency, self.drop_bandwidth, self.drop_s_factor, self.text_preamble_l, self.text_sync_word]),
            widgets.HBox([self.input_user, self.btn_send_command, self.btn_clear_output]), 
            self.output_terminal
        ]))
    
    def display_ui_wireshark(self):
        display(widgets.VBox([
            widgets.HBox([self.btn_run_pycat, self.btn_stop_pycat]), 
            self.output_wireshark
        ]))
    
    def display_ui_cmd_decode_tm(self):
        display(widgets.VBox([
            widgets.HBox([self.text_payload, self.text_ext_key, self.btn_decode]), 
            self.output_decoded_tm
        ]))
        
    def display_ui_live_decoding(self):
        display(widgets.VBox([
            widgets.HBox([self.text_frequency_decoder, self.dropdown_preset_decoder, self.btn_run_decode, self.btn_stop_decode ]), 
            self.btn_clear_decoder_output,
            self.output_live_decoder
        ]))     
class HandsOn2CatsnifferUI:
    def __init__(self):
        self.nb = Notebook()
        # ======= UI Terminal ========
        self.output_terminal   = widgets.Output(layout=widgets.Layout(width='100%', height='500px', border="1px solid black", overflow='scroll'))
        self.btn_port          = widgets.Button(description="Scan ports")
        self.dropdown_channel    = widgets.Dropdown(options=[i for i in range(11, 27)], value=25, description='Channel:', layout=widgets.Layout(width='25%'))
        self.input_user        = widgets.Text(placeholder="Type the command", layout=widgets.Layout(width='25%'))
        self.btn_clear_output  = widgets.Button(description="Clear console", icon="eraser")
        self.btn_loop_read     = widgets.Button(description="Open", icon="play-circle", button_style="success")
        self.dropdown_ports    = widgets.Dropdown(options=self.nb.detect_serial_ports(None), description='Ports:', layout=widgets.Layout(width='25%'))
        
        self.sniffer_thread = threading.Thread()
        self.sniffer_process = False
        self.sniffer_status = False
        
        self.btn_port.on_click(self._on_scan_port)
        self.btn_clear_output.on_click(self._on_clear_output)
        self.btn_loop_read.on_click(self._on_loop_reading)
        self._on_scan_port(None)
        
    
    def _loop_sniffer_worker(self):
        try:
            cmd = [PYTHON_ENV, os.path.join(PYCATSNIFF_PATH, "cat_sniffer.py"), "sniff", self.dropdown_ports.value, "-ff", "-ws", "-phy", "zigbee", "-ch", str(self.dropdown_channel.value)]
            self.output_terminal.append_stdout(f"> {' '.join(cmd)}\n")
            self.sniffer_process = subprocess.run(cmd)
        except NameError:
            self.output_terminal.append_stdout("Please run the block code of the terminal above, and select the communication port\n")
    
    def _show_prompt_catsniffer(self, data):
        prompt = f"\n[CATSNIFFER] {data}"
        self.output_terminal.append_stdout(prompt)
    
    def _show_prompt_user(self, data):
        prompt = f"> {data}\n"
        self.output_terminal.append_stdout(prompt)
    
    def _on_scan_port(self, _):
        self.dropdown_ports.options = self.nb.detect_serial_ports(None)

    def _on_clear_output(self, _):
        self.output_terminal.clear_output()
    
    def _on_loop_reading(self, _):
        self.sniffer_status = not self.sniffer_status
        
        if self.sniffer_status:
            if not self.sniffer_thread.is_alive():
                self.sniffer_thread = threading.Thread(target=self._loop_sniffer_worker)
                self.sniffer_thread.start()
                self.btn_loop_read.description = "Close"
                self.btn_loop_read.icon="stop-circle"
                self.btn_loop_read.button_style='danger'
        else:
            self.btn_loop_read.description = "Open"
            self.btn_loop_read.icon="play-circle"
            self.btn_loop_read.button_style='success'
            if self.sniffer_thread and self.sniffer_thread.is_alive():
                self.sniffer_thread.join(timeout=1)
    
    def display_ui_terminal(self):
        display(widgets.VBox([
            widgets.HBox([self.btn_port, self.dropdown_ports, self.dropdown_channel, self.btn_loop_read, self.btn_clear_output]),
            self.output_terminal
        ]))
        
class HandsOn3CatsnifferUI:
    def __init__(self):
        self.nb = Notebook()
        self.ser = SerialConnection()
        # ======= UI Terminal ========
        self.output_terminal   = widgets.Output(layout=widgets.Layout(width='100%', height='500px', border="1px solid black", overflow='scroll'))
        self.btn_port          = widgets.Button(description="Scan ports")
        self.input_user        = widgets.Text(value="gattcmd_", placeholder="Type the command", layout=widgets.Layout(width='25%'))
        self.btn_send_command  = widgets.Button(description="Send", icon="arrow-right")
        self.btn_clear_output  = widgets.Button(description="Clear console", icon="eraser")
        self.btn_loop_read     = widgets.Button(description="Open", icon="play-circle", button_style="success")
        self.btn_open_ws       = widgets.Button(description="Open Wireshark", icon="eye", button_style="primary")
        self.dropdown_ports    = widgets.Dropdown(options=self.nb.detect_serial_ports(None), description='Ports:', layout=widgets.Layout(width='40%'))
        self.dropdown_baudrate = widgets.Dropdown(options=[9600, 19200, 115200, 921600 ], value=921600, description='Baudrate:', layout=widgets.Layout(width='40%'))
        
        self.loop_thread = threading.Thread()
        self.loop_reading = False
        self.start_command = False
        
        self.btn_port.on_click(self._on_scan_port)
        self.btn_send_command.on_click(self._on_send_command)
        self.btn_clear_output.on_click(self._on_clear_output)
        self.btn_loop_read.on_click(self._on_loop_reading)
        self.btn_open_ws.on_click(self._on_open_ws)
        self._on_scan_port(None)
        
    def _loop_reading_worker(self):
        if self.ser.connect(port=self.dropdown_ports.value, baudrate=self.dropdown_baudrate.value):
            if self.start_command:
                self.ser.send_command_string("gattcmd_scan")
            while self.loop_reading:
                data = self.ser.serial_conn.readline()
                if data:
                    self.output_terminal.append_stdout(data.decode("utf-8", errors="ignore"))
                time.sleep(0.1)
            self.ser.disconnect()
    
    def _show_prompt_user(self, data):
        prompt = f"> {data}\n"
        self.output_terminal.append_stdout(prompt)
    
    def _on_open_ws(self, _):
        if platform.system() == "Windows":
            cmd = [WS_WINDOWS_PATH]
        elif platform.system() == "Linux":
            cmd = [WS_LINUX_PATH]
        elif platform.system() == "Darwin":
            cmd = [WS_MACOS_PATH]
        else:
            print("Not supported OS")
            return
        _ = self.nb.run_process_cmd(cmd)
    
    def _on_scan_port(self, _):
        self.dropdown_ports.options = self.nb.detect_serial_ports(None)
    
    def _on_send_command(self, _):
        cmd = self.input_user.value
        self.ser.send_command_string(cmd)
        self.input_user.value = ""

    def _on_clear_output(self, _):
        self.output_terminal.clear_output()
    
    def _on_loop_reading(self, _):
        self.loop_reading = not self.loop_reading
        
        if self.loop_reading:
            if not self.loop_thread.is_alive():
                self.loop_thread = threading.Thread(target=self._loop_reading_worker)
                self.loop_thread.start()
                self.btn_loop_read.description = "Close"
                self.btn_loop_read.icon="stop-circle"
                self.btn_loop_read.button_style='danger'
        else:
            self.btn_loop_read.description = "Open"
            self.btn_loop_read.icon="play-circle"
            self.btn_loop_read.button_style='success'
    
    def display_ui_minino_terminal(self, start_command = False):
        self.start_command = start_command
        display(widgets.VBox([
            widgets.Box([self.btn_port, self.dropdown_ports, self.dropdown_baudrate, self.btn_loop_read]),
            widgets.HBox([self.input_user, self.btn_send_command, self.btn_clear_output]), 
            self.output_terminal
        ]))
    
    def display_open_wireshark_btn(self):
        display(self.btn_open_ws)
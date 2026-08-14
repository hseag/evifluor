# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

import random
import shlex
import socket
import threading
from enum import IntEnum

from hse.simulator.compare import compare_measurement_files

SIMULATOR_HOST = "127.0.0.1"
SIMULATOR_PORT = 5000


class Error(IntEnum):
    EVI_OK = 0
    EVI_UNKNOWN_COMMAND = 1
    EVI_INVALID_PARAMETER = 2
    EVI_SREC_FLASH_WRITE_ERROR = 4
    EVI_SREC_UNSUPPORTED_TYPE = 5
    EVI_SREC_INVALID_CRC = 6
    EVI_SREC_INVALID_STRING = 7
    EVI_NO_MORE_LOGGING = 11


class CommonIndex(IntEnum):
    VERSION = 0
    SERIALNUMBER = 1
    PRODUCTIONNUMBER = 3
    QC_MODE = 4


class ValueType(IntEnum):
    STRING = 0
    UINT32 = 1
    DOUBLE = 2


class SimulationBase:
    def __init__(self):
        self._is_in_qc_mode = False
        self._logged_messages = []
        self._stop_event = threading.Event()
        self._server_socket = None
        self._verbose = False
        self._data = []
        self._should_abort = False
        self._cuvette_holder_empty = 1

    def reset_state(self):
        self._data = []
        self._cuvette_holder_empty = 1
        self._logged_messages = []

    def device_name(self):
        return "common"

    def random_number(self, a, b):
        return round(random.randrange(a, b) + random.random(), 2)

    def random_number_as_int(self, a, b):
        return int(round(random.randrange(a, b) + random.random(), 0))

    def set_value_command(self, index, value) -> str:
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def get_value_command(self, index) -> str:
        if index == CommonIndex.VERSION:
            return "V 9.9.9"
        if index == CommonIndex.SERIALNUMBER:
            return "V SIMULATOR"
        if index == CommonIndex.PRODUCTIONNUMBER:
            return "V PRODUCTIONNUMBER"
        if index == CommonIndex.QC_MODE:
            return "V 1" if self._is_in_qc_mode else "V 0"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_value_command(self, args) -> str:
        if len(args) == 3:
            return self.set_value_command(int(args[1]), int(args[2]))
        if len(args) == 2:
            return self.get_value_command(int(args[1]))
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def get_value_type_command(self, index) -> str:
        if index in [CommonIndex.VERSION, CommonIndex.SERIALNUMBER, CommonIndex.PRODUCTIONNUMBER]:
            return f"H {ValueType.STRING}"
        if index == CommonIndex.QC_MODE:
            return f"H {ValueType.UINT32}"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def selftest_command(self) -> str:
        return "Y 0"

    def get_cuvette_holder_empty_command(self) -> str:
        return f"X {self._cuvette_holder_empty}"

    def add_logging_message(self, message):
        self._logged_messages.append(message)
        if len(self._logged_messages) > 5000:
            del self._logged_messages[0]

    def logging_command(self, message) -> str:
        if message is None:
            if len(self._logged_messages) == 0:
                return f"E {Error.EVI_NO_MORE_LOGGING}"
            message = self._logged_messages[0]
            del self._logged_messages[0]
            return f'Q "{message}"'
        self.add_logging_message(message)
        return "Q"

    def handle_type_command(self, args) -> str:
        if len(args) == 2:
            return self.get_value_type_command(int(args[1]))
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_selftest_command(self, args) -> str:
        if len(args) == 1:
            return self.selftest_command()
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_logging_command(self, args) -> str:
        if len(args) == 1:
            return self.logging_command(None)
        if len(args) == 2:
            return self.logging_command(args[1])
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_cuvette_holder_empty_command(self, args) -> str:
        if len(args) == 1:
            return self.get_cuvette_holder_empty_command()
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def load_data(self, data_file) -> bool:
        if self._verbose:
            print(f"{self.__class__.__name__}.load_data({data_file})")
        return False

    def handle_control_command(self, args) -> str:
        if len(args) == 2 and args[1] == "EXIT":
            if self._verbose:
                print("Simulator EXIT")
            self._should_abort = True
            return "! 0"
        if len(args) == 2 and args[1] == "RESET":
            if self._verbose:
                print("Simulator RESET")
            self.reset_state()
            self.measure_always_zero = False
            return "! 0"
        if len(args) == 3 and args[1] == "CHECKEMPTY":
            if args[2] not in ["0", "1"]:
                return f"E {Error.EVI_INVALID_PARAMETER}"
            self._cuvette_holder_empty = int(args[2])
            return "! 0"
        if len(args) == 3 and args[1] == "ZERO":
            if args[2] not in ["0", "1"]:
                return f"E {Error.EVI_INVALID_PARAMETER}"
            self.measure_always_zero = bool(int(args[2]))
            return "! 0"
        if len(args) == 3 and args[1] == "SKIP":
            skip_count = int(args[2])
            for _ in range(skip_count):
                if len(self._data) > 0:
                    del self._data[0]
            return "! 0"
        if len(args) == 3 and args[1] == "LOAD":
            if self._verbose:
                print(f"Simulator load file {args[2]}")
            try:
                self.load_data(args[2])
            except Exception as exc:
                print(f"Error loading data file {args[2]} - {exc}")
                return "! 990 " + f"Error loading data file {args[2]} - {exc}"
            return "! 0"
        if args[1] == "COMPARE":
            if len(args) < 5:
                return f"E {Error.EVI_INVALID_PARAMETER}"
            device_name = args[2]
            file_a = args[3]
            file_b = args[4]
            skip_a = 0
            skip_b = 0
            no_air = False
            extra = args[5:]
            if "--no_air" in extra:
                no_air = True
                extra = [arg for arg in extra if arg != "--no_air"]
            if len(extra) == 2:
                skip_a = int(extra[0])
                skip_b = int(extra[1])
            elif len(extra) != 0:
                return f"E {Error.EVI_INVALID_PARAMETER}"
            if self._verbose:
                print(
                    f"Simulator compare device={device_name} a={file_a} b={file_b} "
                    f"skipa={skip_a} skipb={skip_b} no_air={no_air}"
                )
            try:
                return "! 0" if compare_measurement_files(file_a, file_b, device_name, skip_a, skip_b, no_air) else "! 1"
            except Exception:
                return "! 991"
        return f"E {Error.EVI_INVALID_PARAMETER}"

    def handle_command(self, args) -> str:
        if args[0] == "!":
            return self.handle_control_command(args)
        if args[0] == "V":
            return self.handle_value_command(args)
        if args[0] == "H":
            return self.handle_type_command(args)
        if args[0] == "Y":
            return self.handle_selftest_command(args)
        if args[0] == "Q":
            return self.handle_logging_command(args)
        if args[0] == "X":
            return self.handle_cuvette_holder_empty_command(args)
        return f"E {Error.EVI_UNKNOWN_COMMAND}"

    def handle_client_connection(self, conn, addr):
        if self._verbose:
            print(f"Connection from {addr}")

        class ReadState(IntEnum):
            IDLE = 0
            READ = 1

        rx_buffer = bytearray()
        read_state = ReadState.IDLE

        with conn:
            while not self._should_abort:
                data = conn.recv(1024)
                if len(data) == 0:
                    return
                byte_array = bytearray(data)
                for byte in byte_array:
                    if read_state == ReadState.IDLE:
                        if byte == (b":")[0]:
                            rx_buffer = bytearray()
                            read_state = ReadState.READ
                    elif read_state == ReadState.READ:
                        if byte == (b"\n")[0] or byte == (b"\r")[0]:
                            request = rx_buffer.decode("utf-8")
                            response = self.handle_command(shlex.split(request))
                            if self._verbose:
                                print(f"{request} -> {response}")
                            conn.sendall((":" + response + "\n").encode())
                            rx_buffer = bytearray()
                            read_state = ReadState.IDLE
                        else:
                            rx_buffer.append(byte)

    def stop(self):
        self._stop_event.set()
        if self._server_socket is not None:
            try:
                self._server_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                self._server_socket.close()
            except OSError:
                pass

    def start_server(self, verbose):
        self._verbose = verbose
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            self._server_socket = server_socket
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((SIMULATOR_HOST, SIMULATOR_PORT))
            server_socket.listen()
            server_socket.settimeout(0.2)
            try:
                while not (self._stop_event.is_set() or self._should_abort):
                    try:
                        conn, addr = server_socket.accept()
                    except socket.timeout:
                        continue
                    except OSError:
                        break
                    threading.Thread(target=self.handle_client_connection, args=(conn, addr), daemon=False).start()
            finally:
                self._server_socket = None

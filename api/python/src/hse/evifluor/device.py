# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

import shlex
import socket
import time

import serial
import serial.tools.list_ports

from hse.evifluor.channel import Channel
from hse.evifluor.constants import (
    DictKeys,
    Error,
    Index,
    Selftest,
    TypeOf,
    USB,
)
from hse.evifluor.singlemeasurement import SingleMeasurement


class AutoGainResult:
    """Represents the result of an automatic gain adjustment operation."""

    def __init__(self, found, led_power):
        """Initializes an auto-gain result.

        Args:
            found: Indicates whether the optimal gain setting was found.
            led_power: LED power level determined during auto-gain.
        """
        self.found    = found
        self.led_power = led_power

    def __repr__(self):
        """Returns a string representation of the auto-gain result."""
        return "found:{} led_power:{}".format(self.found, self.led_power)

    def to_json(self):
        """Converts the auto-gain result to a JSON representation."""
        ret = {}
        ret[DictKeys.AUTOGAIN_RESULT_FOUND] = self.found
        ret[DictKeys.AUTOGAIN_RESULT_LED_POWER] = self.led_power
        return ret
        

class FirstAirMeasurementResult:
    """Represents the first air measurement with minimum and maximum recorded measurements."""

    def __init__(self, min_measurement, max_measurement):
        """Initializes a first-air measurement result.

        Args:
            min_measurement: Measurement recorded at minimum LED power.
            max_measurement: Measurement recorded at maximum LED power.
        """
        self.min_measurement = min_measurement
        self.max_measurement = max_measurement

    def __repr__(self):
        """Returns a string representation of the first air measurement result."""
        return "min:{} max:{}".format(self.min_measurement, self.max_measurement)
        
    def adjust_to_led_power(self, led_power):
        """Adjusts the measurement to a given LED power level.

        Args:
            led_power: Target LED power level.

        Returns:
            A :class:`SingleMeasurement` adjusted to ``led_power``.
        """
        denominator = self.max_measurement.channel_470.led_power - self.min_measurement.channel_470.led_power
        if denominator == 0:
            return SingleMeasurement(self.min_measurement)
        dark  = self.min_measurement.channel_470.dark  + (self.max_measurement.channel_470.dark  - self.min_measurement.channel_470.dark)  / (denominator) * (led_power - self.min_measurement.channel_470.led_power)
        value = self.min_measurement.channel_470.value + (self.max_measurement.channel_470.value - self.min_measurement.channel_470.value) / (denominator) * (led_power - self.min_measurement.channel_470.led_power)
        channel_470 = Channel(dark, value, led_power)
        return SingleMeasurement(channel_470)

    def to_json(self):
        """Converts the first air measurement result to a JSON representation."""
        ret = {}
        ret[DictKeys.MIN_MEASUREMENT] = self.min_measurement.to_json()
        ret[DictKeys.MAX_MEASUREMENT] = self.max_measurement.to_json()
        return ret


class FirstSampleMeasurementResult:
    """Represents the result of the first sample measurement, including auto-gain data."""

    def __init__(self, auto_gain_result, measurement):
        """Initializes a first-sample measurement result.

        Args:
            auto_gain_result: Auto-gain result of the sample measurement.
            measurement: Recorded sample measurement.
        """
        self.auto_gain_result = auto_gain_result
        self.measurement    = measurement

    def __repr__(self):
        """Returns a string representation of the first sample measurement result."""
        return "auto_gain_result:{} measurement:{}".format(self.auto_gain_result, self.measurement)


class SelfttestResult:
    """Represents the aggregated flags resulting from a device self-test."""

    def __init__(self, result):
        """Initializes the self-test result.

        Args:
            result: Raw result bit mask returned by the device self-test.
        """
        self.result = result
        
    def has_problems(self):
        """Determines whether there are any problems in the self-test."""
        return self.result != 0

    def has_communication_error(self):
        """Checks if there is a problem with the communication channel."""
        return bool(self.result & Selftest.COMUNICATION_ERROR)
        
    def to_json(self):
        """Converts the self-test result to a JSON representation."""
        ret = {}
        ret[DictKeys.SELFTEST_RESULT] = self.result
        return ret
        

class Device:
    """Represents the eviFluor module device API."""
    def __init__(self, device = None):
        """Initializes a device connection.

        Args:
            device: Optional device serial number or ``"SIMULATION"`` for socket
                mode. If omitted, the implementation auto-detects a device.
        """
        if device == "SIMULATION":
            self.is_simulation = True
            self.device = "SOCKET"
            self._simulation_socket = None
            self._simulation_rx_buffer = bytearray()
        else:
            self.is_simulation = False
            self.device = self.find_device(device)
            if self.device is None:
                raise Exception("eviFluor Module not found!")
            
            self.serial = serial.Serial(self.device, 115200, timeout=30)
            self.serial.reset_input_buffer()

    def find_device(self, device = None):
        """Finds a matching serial device.

        Args:
            device: Optional serial number used to filter matching devices.

        Returns:
            The matching serial port name, or ``None`` if no device was found.
        """
        ports = serial.tools.list_ports.comports()
        for p in ports:
            if p.vid == USB.VID and p.pid == USB.PID and (device == None or device == p.serial_number):
                return p.device
        return

    def error2text(self, error):
        """Converts a device error code into human-readable text.

        Args:
            error: Numeric error code returned by the device protocol.

        Returns:
            A human-readable description of the error.
        """
        if error == Error.OK:
            return "OK"
        elif error == Error.UNKNOWN_COMMAND:
            return "Unknown command"
        elif error == Error.INVALID_PARAMETER:
            return "Invalid parameter"
        elif error == Error.TIMEOUT:
            return "Timeout"
        elif error == Error.SREC_FLASH_WRITE_ERROR:
            return "SREC Flash write error"
        elif error == Error.SREC_UNSUPPORTED_TYPE:
            return "SREC Unsupported type"
        elif error == Error.SREC_INVALID_CRC:
            return "SREC Invalid crc"
        elif error == Error.SREC_INVALID_STRING:
            return "SREC Invalid string"
        else:
            return "?"

    def command(self, tx):
        """Sends a command to the device and returns the tokenized response.

        Args:
            tx: Command string to transmit without prefix or trailing newline.

        Returns:
            Parsed response tokens returned by the device.
        """
        if self.is_simulation:
            return self.command_socket(tx)
        else:
            return self.command_serial(tx)

    def _ensure_simulation_connection(self):
        """Opens the simulator TCP connection on first use and keeps it for the device lifetime."""
        if self._simulation_socket is not None:
            return

        self._simulation_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._simulation_socket.settimeout(30)
        self._simulation_socket.connect(("localhost", 5000))
        self._simulation_rx_buffer = bytearray()

    def _simulation_readline(self):
        """Reads one newline-terminated response from the persistent simulator socket."""
        while True:
            newline_index = self._simulation_rx_buffer.find(b"\n")
            if newline_index >= 0:
                line = bytes(self._simulation_rx_buffer[: newline_index + 1])
                del self._simulation_rx_buffer[: newline_index + 1]
                return line

            chunk = self._simulation_socket.recv(1024)
            if not chunk:
                return b""
            self._simulation_rx_buffer.extend(chunk)

    def command_socket(self, tx):
        """Transmits a command to the simulator over TCP.

        Args:
            tx: Command string to transmit.

        Returns:
            Parsed response tokens returned by the simulator.
        """
        self._ensure_simulation_connection()
        self._simulation_socket.sendall((":" + tx + "\n").encode())
        while True:
            rx = self._simulation_readline()
            if not rx:
                self.close()
                raise Exception("No response within time!")
            if rx[0] != (b':')[0] :
                self.close()
                raise Exception(("Response did not start with ':' {}!").format(rx))
            ba = bytearray(rx)
            if rx[1] == (b'#')[0]:
                print("DEBUG", rx)
            else:
                del ba[0]
                #parts = (ba.decode("utf-8")).split()
                parts = shlex.split(ba.decode("utf-8"))
                if parts[0] == "E":
                    raise Exception("Response of TX:{} has an error: ({}) {}!".format(tx, rx, self.error2text(int(parts[1]))))
                break
        return parts

    def command_serial(self, tx):
        """Transmits a command over the serial connection.

        Args:
            tx: Command string to transmit.

        Returns:
            Parsed response tokens returned by the device.
        """
        self.serial.write((":" + tx + "\n").encode())
        while True:
            rx = self.serial.readline()
            if rx == '':
      	        raise Exception("No response within time!")
            if rx[0] != (b':')[0] :
                raise Exception(("Response did not start with ':' {}!").format(rx))
            ba = bytearray(rx)
            if rx[1] == (b'#')[0]:
                print("DEBUG", rx)
            else:
                del ba[0]
                #parts = (ba.decode("utf-8")).split()
                parts = shlex.split(ba.decode("utf-8"))
                if parts[0] == "E":
                    raise Exception("Response of TX:{} has an error: ({}) {}!".format(tx, rx, self.error2text(int(parts[1]))))
                break
        return parts

    def get(self, index):
        """Retrieves a value from the device at the specified index.

        Args:
            index: Protocol index to read from the device.

        Returns:
            The value converted to the type reported by the device.
        """
        response = self.command(("V {}").format(index))
        typeof   = self.typeof(index)
        if typeof == TypeOf.STRING:
            return response[1]
        elif typeof == TypeOf.UINT32:
            return int(response[1])
        elif typeof == TypeOf.DOUBLE:
            return float(response[1])
        else:
            return response[1]
            
    def set(self, index, value):
        """Sets a value on the device at the specified index.

        Args:
            index: Protocol index to update.
            value: Value to write at ``index``.
        """
        self.command(("V {} {}").format(index, value))

    def typeof(self, index):
        """Returns the data type stored at the specified index.

        Args:
            index: Protocol index to inspect.

        Returns:
            Numeric type identifier reported by the device.
        """
        response = self.command(("H {}").format(index))
        return int(response[1])

    def serial_number(self):
        """Retrieves the serial number of the connected device."""
        return self.get(Index.SERIALNUMBER)

    def firmware_version(self):
        """Retrieves the firmware version of the connected device."""
        return self.get(Index.VERSION)

    def production_number(self):
        """Retrieves the production number of the connected device."""
        return self.get(Index.PRODUCTIONNUMBER)

    def __repr__(self):
        """Returns a textual representation of the connected device."""
        return "eviFluor Module@{} SN:{} Version:{}".format(self.device, self.serial_number(), self.firmware_version())

    def close(self):
        """Closes the serial connection if the device owns one."""
        if self.is_simulation:
            if getattr(self, "_simulation_socket", None) is not None:
                self._simulation_socket.close()
                self._simulation_socket = None
            self._simulation_rx_buffer = bytearray()
            return
        if hasattr(self, "serial"):
            self.serial.close()

    def baseline(self):
        """Executes the baseline command to clear internal measurement memory."""
        response = self.command("G")

    def is_cuvette_holder_empty(self):
        """Checks whether the cuvette holder is empty."""
        response = self.command("X")
        return ((int)(response[1]) == 1)

    def autogain(self, level):
        """Performs an auto-gain operation at the specified level.

        Args:
            level: Gain target in the range 0..2500.

        Returns:
            An :class:`AutoGainResult` indicating success and LED power.
        """
        response = self.command("C {}".format(level))
        
        if int(response[1]) == 0:
            return AutoGainResult(False, int(response[2]))
        else:
            return AutoGainResult(True, int(response[2]))

    def measure(self, last = -1):
        """Performs a measurement and retrieves the channel values.

        Args:
            last: Optional protocol parameter selecting a previous measurement.
                A negative value performs a fresh measurement.

        Returns:
            A :class:`SingleMeasurement` with the measured channel values.
        """
        command = "M"
        if last >= 0:
            command = command + (" {}").format(last)
        response = self.command(command)
        ret = {}
        channel470 = Channel(float(response[1]), float(response[2]), float(response[3]))
        return SingleMeasurement(channel470)
        
    def first_air_measurement(self):
        """Performs the first air measurement at minimum and maximum LED power levels."""
        power_min = self.get(Index.CURRENT_LED470_POWER_MIN)
        power_max = self.get(Index.CURRENT_LED470_POWER_MAX)
        
        self.set(Index.CURRENT_LED470_POWER, power_min)
        min_measurement = self.measure()
      
        self.set(Index.CURRENT_LED470_POWER, power_max)
        max_measurement = self.measure()

        return FirstAirMeasurementResult(min_measurement, max_measurement)

    def first_sample_measurement(self, factor = 0.8):
        """Performs the first sample measurement using auto-gain.

        Args:
            factor: Scaling factor used to derive the initial auto-gain target.

        Returns:
            A :class:`FirstSampleMeasurementResult` containing auto-gain and
            measurement data.
        """
        auto_gain_result = self.autogain(int(2500 * factor))
        measurement      = self.measure()
        return FirstSampleMeasurementResult(auto_gain_result, measurement)

    def verify(self):
        """Verifies the integrity of the current firmware image."""
        response = self.command("T")
        return ((int)(response[1]) == 1)

    def reboot(self):
        """Reboots the device."""
        response = self.command("R")

    def erase(self):
        """Erases the secondary firmware image on the device."""
        response = self.command("F")
        
    def fwupdate(self, filename):
        """Streams an SREC file to the device and performs a firmware update.

        Args:
            filename: Path to the firmware image file to send to the device.
        """
        with open(filename, 'r') as file:
            self.erase()
            for srecLine in file:
                self.command("S {}".format(srecLine))
            if not self.verify():
                raise Exception("Firmware update failed. Image not valid!")
                
            self.reboot()
            self.serial.close()
            del self.serial
            time.sleep(30.0)
            
            #After a reboot we have to re-open the serial device
            self.serial = serial.Serial(self.device, 115200, timeout=30)
            self.serial.reset_input_buffer()

            if self.verify():
                raise Exception("Firmware update failed. Image still valid!")
            
    def selftest(self):
        """Runs the device self-test and returns the aggregated result."""
        response = self.command("Y")
        return SelfttestResult(int(response[1]))

    def technical_report(self):
        """Builds a technical report containing measurement and device metadata."""
        result = {}
        result[DictKeys.MEASURE]          = self.first_air_measurement().to_json()
        result[DictKeys.SELFTEST]         = self.selftest().to_json()
        result[DictKeys.SERIALNUMBER]     = self.serial_number()
        result[DictKeys.FIRMWAREVERSION]  = self.firmware_version()
        result[DictKeys.PRODUCTIONNUMBER] = self.production_number()
        return result

    def set_status_led(self, color):
        """Sets the status LED color.

        Args:
            color: Numeric color value understood by the device firmware.
        """
        self.command("Z {}".format(color))
        
    def logging(self):
        """Retrieves log messages accumulated on the device."""
        messages = []
        while True:
            try:
                response = self.command("Q")
                messages.append(response[1])
            except Exception:
                break
        return messages
        

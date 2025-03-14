// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;
using System.Collections.Generic;
using System.IO.Ports;
using System.Management;
using System.Text.Json.Nodes;

namespace Hse.EviFluor;

/// <summary>
/// Represents the result of an automatic gain adjustment operation.
/// </summary>
public class AutoGainResult
{
    /// <summary>
    /// Indicates whether the optimal gain setting was found.
    /// </summary>
    public bool Found { get; set; }

    /// <summary>
    /// The LED power level determined during the auto-gain adjustment.
    /// </summary>
    public int LedPower { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="AutoGainResult"/> class.
    /// </summary>
    /// <param name="found">Indicates if the gain setting was successfully found.</param>
    /// <param name="ledPower">The LED power level used.</param>
    public AutoGainResult(bool found, int ledPower)
    {
        Found = found;
        LedPower = ledPower;
    }

    /// <summary>
    /// Returns a string representation of the auto-gain result.
    /// </summary>
    /// <returns>A formatted string displaying the gain result.</returns>
    public override string ToString()
    {
        return $"Found:{Found} LedPower:{LedPower}";
    }
}

/// <summary>
/// Represents the result of the first air measurement, containing the minimum and maximum recorded measurements.
/// </summary>
public class FirstAirMeasurementResult
{
    /// <summary>
    /// The minimum recorded measurement.
    /// </summary>
    public SingleMeasurement MinMeasurement { get; set; }

    /// <summary>
    /// The maximum recorded measurement.
    /// </summary>
    public SingleMeasurement MaxMeasurement { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FirstAirMeasurementResult"/> class.
    /// </summary>
    /// <param name="minMeasurement">The minimum recorded measurement.</param>
    /// <param name="maxMeasurement">The maximum recorded measurement.</param>
    public FirstAirMeasurementResult(SingleMeasurement minMeasurement, SingleMeasurement maxMeasurement)
    {
        MinMeasurement = minMeasurement;
        MaxMeasurement = maxMeasurement;
    }

    /// <summary>
    /// Returns a string representation of the first air measurement result.
    /// </summary>
    /// <returns>A formatted string displaying the min and max measurements.</returns>
    public override string ToString()
    {
        return $"MinMeasurement:{MinMeasurement} MaxMeasurement:{MaxMeasurement}";
    }

    /// <summary>
    /// Adjusts the measurement to a given LED power level using linear interpolation.
    /// </summary>
    /// <param name="ledPower">The target LED power level.</param>
    /// <returns>A new <see cref="SingleMeasurement"/> adjusted to the specified LED power.</returns>
    public SingleMeasurement AdjustToLedPower(int ledPower)
    {
        var dark = MinMeasurement.Channel470.Dark + (MaxMeasurement.Channel470.Dark - MinMeasurement.Channel470.Dark) / (MaxMeasurement.Channel470.LedPower - MinMeasurement.Channel470.LedPower) * (ledPower - MinMeasurement.Channel470.LedPower);
        var value = MinMeasurement.Channel470.Value + (MaxMeasurement.Channel470.Value - MinMeasurement.Channel470.Value) / (MaxMeasurement.Channel470.LedPower - MinMeasurement.Channel470.LedPower) * (ledPower - MinMeasurement.Channel470.LedPower);
        var channel470 = new Channel(dark, value, ledPower);
        return new SingleMeasurement(channel470);
    }

    /// <summary>
    /// Converts the FirstAirMeasurementResult values to a JSON representation.
    /// </summary>
    /// <returns>A JsonNode representing the channel values.</returns>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();
        obj[Dict.MIN_MEASUREMENT] = MinMeasurement.ToJson();
        obj[Dict.MAX_MEASUREMENT] = MaxMeasurement.ToJson();
        return obj;
    }
}

/// <summary>
/// Represents the result of the first sample measurement, containing auto-gain results and the measurement itself.
/// </summary>
public class FirstSampleMeasurementResult
{
    /// <summary>
    /// The auto-gain result of the sample measurement.
    /// </summary>
    public AutoGainResult AutoGainResult { get; set; }

    /// <summary>
    /// The recorded sample measurement.
    /// </summary>
    public SingleMeasurement Measurement { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="FirstSampleMeasurementResult"/> class.
    /// </summary>
    /// <param name="autoGainResult">The auto-gain result of the sample measurement.</param>
    /// <param name="measurement">The recorded sample measurement.</param>
    public FirstSampleMeasurementResult(AutoGainResult autoGainResult, SingleMeasurement measurement)
    {
        AutoGainResult = autoGainResult;
        Measurement = measurement;
    }

    /// <summary>
    /// Returns a string representation of the first sample measurement result.
    /// </summary>
    /// <returns>A formatted string displaying the auto-gain result and the measurement.</returns>
    public override string ToString()
    {
        return $"AutoGainResult:{AutoGainResult} Measurement:{Measurement}";
    }
}

/// <summary>
/// Represents the result of a self-test, containing various checks and problem indicators.
/// </summary>
public class SelfTestResult
{
    /// <summary>
    /// Gets or sets the integer result of the self-test.
    /// </summary>
    public int Result { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="SelfTestResult"/> class.
    /// </summary>
    /// <param name="result">The result of the self-test.</param>
    public SelfTestResult(int result)
    {
        Result = result;
    }

    /// <summary>
    /// Determines whether there are any problems in the self-test.
    /// </summary>
    /// <returns>True if there are problems; otherwise, false.</returns>
    public bool HasProblems()
    {
        return Result != 0;
    }

    /// <summary>
    /// Checks if there is a problem with the communication.
    /// </summary>
    public bool HasProblemWithCommunication() => (Result & (int)Selftest.COMUNICATION_ERROR) != 0;

    /// <summary>
    /// Converts the self-test result to a JSON representation.
    /// </summary>
    /// <returns>A JsonNode representing the self-test result.</returns>
    public JsonNode ToJson()
    {
        JsonObject obj = new JsonObject();
        obj[Dict.SELFTEST_RESULT] = Result;
        return obj;
    }
}

/// <summary>
/// This class represents the eviFluor module.
/// </summary>
public class Device : IDisposable
{
    private SerialPort serialPort_;
    private string serialNumber_ = "?";
    private string firmwareVersion_ = "?";

    public void Dispose()
    {
        if (serialPort_ != null && serialPort_.IsOpen)
            serialPort_.Close();

        if (serialPort_ != null)
            serialPort_.Dispose();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="Device"/> class.
    /// The constructor attempts to connect to an EviFluor module via a serial port.
    /// If no serial port is provided, it tries to auto-detect the device.
    ///
    /// Throws an exception if:
    /// - No device is found during auto-detection.
    /// - The provided serial port does not match the expected VID/PID for the EviFluor device.
    /// </summary>
    /// <param name="serialNumber">
    /// The serial number of the device to connect to. If null or empty, the constructor
    /// attempts to automatically find a device.
    /// </param>
    /// <exception cref="Exception">
    /// Thrown when:
    /// - No device is found during auto-detection (if <paramref name="serialPortName"/> is null or empty).
    /// - The provided serial port does not correspond to an EviFluor device.
    /// </exception>
    public Device(string? serialNumber = null)
    {
        var serialPortName = FindDevice(serialNumber);
        if (serialPortName == null)
        {
            throw new Exception($"EviFluor ({serialNumber}) module not found");
        }

        serialPort_ = new SerialPort(serialPortName, 115200, Parity.None, 8, StopBits.One)
        {
            ReadTimeout = 30000
        };
        serialPort_.Open();
        serialPort_.DiscardInBuffer();
        serialPort_.DiscardOutBuffer();

        try
        {
            SerialNumber();
            FirmwareVersion();
        }
        catch (Exception)
        {
            // silent fail
        }
    }

    ~Device()
    {
        Dispose();
    }

    public string LibraryVersion
    {
        get
        {
            System.Reflection.Assembly assembly = System.Reflection.Assembly.GetExecutingAssembly();
            System.Diagnostics.FileVersionInfo fvi = System.Diagnostics.FileVersionInfo.GetVersionInfo(assembly.Location);
            return fvi.FileVersion ?? string.Empty;
        }
    }

    /// <summary>
    /// Retrieves a list of available eviFluor devices by scanning serial ports.    
    /// </summary>
    /// <returns>A list of serial numbers of available matching devices.</returns>
    public static List<string> GetAvailableDevices()
    {
        List<string> serialnumbers = new List<string>() { };

        foreach (var port in SerialPort.GetPortNames())
        {
            string serialNumber = "";

            if (IsSerialPortMatchingVidAndPid(port, USB.VID, USB.PID, ref serialNumber))
            {
                serialnumbers.Add(serialNumber);
            }
        }
        return serialnumbers;
    }

    private static string? FindDevice(string? serialNumber)
    {
        foreach (var port in SerialPort.GetPortNames())
        {
            string sn = "";
            if (IsSerialPortMatchingVidAndPid(port, USB.VID, USB.PID, ref sn))
            {
                if (serialNumber == null || sn == serialNumber)
                {
                    return port;
                }
            }
        }

        return null;
    }

    private static bool IsSerialPortMatchingVidAndPid(string portName, int vid, int pid, ref string serialNumber)
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("This functionality is only supported on Windows.");
        }

        string vidAsHex = vid.ToString("X4");
        string pidAsHex = pid.ToString("X4");

        // Query WMI for serial port devices
        using var searcher = new ManagementObjectSearcher(@"SELECT * FROM Win32_PnPEntity WHERE Name LIKE '%(COM%'");
        foreach (var device in searcher.Get())
        {
            var name = device["Name"]?.ToString(); // Friendly name (e.g., "USB Serial Device (COM3)")
            var deviceId = device["DeviceID"]?.ToString(); // Device ID containing VID and PID
            var pnpDeviceId = device["PNPDeviceID"]?.ToString(); // Full PNPDeviceID (useful for extracting serial number)

            if (name != null && name.Contains($"({portName})") && deviceId != null && pnpDeviceId != null)
            {
                // Check if VID and PID match
                var foundVid = ExtractValue(deviceId, "VID_");
                var foundPid = ExtractValue(deviceId, "PID_");
                serialNumber = ExtractSerialNumber(pnpDeviceId);

                if (foundVid == vidAsHex && foundPid == pidAsHex)
                {
                    return true;
                }
            }
        }

        return false;
    }

    private static string ExtractValue(string deviceId, string key)
    {
        var startIndex = deviceId.IndexOf(key) + key.Length;
        return deviceId.Substring(startIndex, 4); // VID and PID are 4 characters long
    }

    private static string ExtractSerialNumber(string pnpDeviceId)
    {
        var parts = pnpDeviceId.Split('\\');
        if (parts.Length > 2)
        {
            return parts[^1]; // Letztes Segment enthält die Seriennummer
        }
        return string.Empty;
    }
    private string[] Command(string tx)
    {
        serialPort_.DiscardInBuffer();
        serialPort_.DiscardOutBuffer();

        tx = $":{tx}";

        serialPort_.WriteLine(tx);

        string rx = serialPort_.ReadLine();
        if (string.IsNullOrEmpty(rx))
            throw new Exception("No response within time!");

        if (!rx.StartsWith(":"))
            throw new Exception($"Response did not start with ':' {rx}");

        string[] parts = rx.Remove(0, 1).Split();

        if (parts[0] == "E")
        {
            int errorCode = -1;

            if (parts.Length >= 2)
                if (int.TryParse(parts[1], out errorCode))
                    throw new Exception($"Response of TX:{tx} has an error: {ErrorToText(errorCode)}");
                else
                    throw new Exception($"Response of TX:{tx} has an unknown error: {rx}");
        }
        else
        {
            if (tx.Remove(0, 1).Split()[0] != parts[0])
            {
                throw new Exception($"Response for sent command '{tx}' does not start with same command: '{rx}'");
            }
        }

        return parts;
    }

    private string ErrorToText(int error)
    {
        switch (error)
        {
            case (int)Error.OK:
                return "OK";

            case (int)Error.UNKNOWN_COMMAND:
                return "Unknown command";

            case (int)Error.INVALID_PARAMETER:
                return "Invalid parameter";

            case (int)Error.SREC_FLASH_WRITE_ERROR:
                return "Invalid parameter";

            case (int)Error.SREC_UNSUPPORTED_TYPE:
                return "SREC: unsupported type";

            case (int)Error.SREC_INVALID_CRC:
                return "SREC: invalid crc";

            case (int)Error.SREC_INVALID_STRING:
                return "SREC: invalid string";

            default:
                return "Unknown error";
        }
    }

    /// <summary>
    /// Retrieves a value from the device at the specified index and converts it to the desired type.
    /// Sends a command to the device to fetch the value and parses the response.
    /// </summary>
    /// <typeparam name="T">
    /// The type to which the retrieved value will be converted. Must be compatible with <see cref="Convert.ChangeType"/>.
    /// </typeparam>
    /// <param name="index">
    /// The index from which the value should be retrieved.
    /// </param>
    /// <returns>
    /// The value retrieved from the device, converted to the specified type <typeparamref name="T"/>.
    /// </returns>
    /// <exception cref="InvalidCastException">
    /// Thrown if the conversion to the specified type <typeparamref name="T"/> fails.
    /// </exception>
    /// <exception cref="Exception">
    /// Thrown if the device response is invalid or does not contain the expected data format.
    /// </exception>
    public T Get<T>(Index index)
    {
        string[] response = Command($"V {(int)index}");
        return (T)Convert.ChangeType(response[1], typeof(T));
    }

    /// <summary>
    /// Sets a value on the device at the specified index.
    /// Sends a command to update the value on the device.
    /// </summary>
    /// <param name="index">The index where the value should be set.</param>
    /// <param name="value">The integer value to set at the specified index.</param>
    public void Set(Index index, int value)
    {
        string[] response = Command($"V {(int)index} {value}");
    }

    /// <summary>
    /// Sets a value on the device at the specified index.
    /// Sends a command to update the value on the device.
    /// </summary>
    /// <param name="index">The index where the value should be set.</param>
    /// <param name="value">The double value to set at the specified index.</param>
    public void Set(Index index, double value)
    {
        string[] response = Command($"V {(int)index} {value}");
    }

    /// <summary>
    /// Sets a value on the device at the specified index.
    /// Sends a command to update the value on the device.
    /// </summary>
    /// <param name="index">The index where the value should be set.</param>
    /// <param name="value">The string value to set at the specified index.</param>
    public void Set(Index index, string value)
    {
        string[] response = Command($"V {(int)index} {value}");
    }

    /// <summary>
    /// Retrieves the serial number of the connected device.
    /// This method uses the <see cref="Get{T}(Index)"/> method to fetch the serial number
    /// from the device at the predefined index for serial numbers.
    /// </summary>
    /// <returns>
    /// The serial number of the device as a string.
    /// </returns>
    /// <exception cref="InvalidCastException">
    /// Thrown if the retrieval or conversion of the serial number fails.
    /// </exception>
    /// <exception cref="Exception">
    /// Thrown if there is an issue communicating with the device or retrieving the value.
    /// </exception>
    public string SerialNumber()
    {
        var serialNumber = Get<string>(Index.SERIALNUMBER);

        // save the serial number for the ToString() function
        serialNumber_ = serialNumber;
        return serialNumber;
    }

    /// <summary>
    /// Retrieves the firmware version of the connected device.
    /// This method uses the <see cref="Get{T}(Index)"/> method to fetch the firmware version
    /// from the device at the predefined index for firmware versions.
    /// </summary>
    /// <returns>
    /// The firmware version of the device as a string.
    /// </returns>
    /// <exception cref="InvalidCastException">
    /// Thrown if the retrieval or conversion of the firmware version fails.
    /// </exception>
    /// <exception cref="Exception">
    /// Thrown if there is an issue communicating with the device or retrieving the value.
    /// </exception>
    public string FirmwareVersion()
    {
        var firmwareVersion = Get<string>(Index.VERSION);

        // save the firmware version for the ToString() function
        serialNumber_ = firmwareVersion;
        return firmwareVersion;
    }

    /// <summary>
    /// Retrieves the production number of the connected device.
    /// This method uses the <see cref="Get{T}(Index)"/> method to fetch the production number
    /// from the device at the predefined index.
    /// </summary>
    /// <returns>
    /// The production number of the device as a string.
    /// </returns>
    /// <exception cref="Exception">
    /// Thrown if there is an issue communicating with the device or retrieving the value.
    /// </exception>
    public string ProductionNumber()
    {
        return Get<string>(Index.PRODUCTIONNUMBER);
    }

    /// <summary>
    /// Performs a self-test on the device and retrieves the result.
    /// </summary>
    /// <returns>
    /// A <see cref="SelfTestResult"/> object containing the parsed self-test result.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown if the response value from the device cannot be parsed as an integer.
    /// </exception>
    /// <exception cref="IndexOutOfRangeException">
    /// Thrown if the device response does not contain the expected number of values.
    /// </exception>
    public SelfTestResult SelfTest()
    {
        string[] response = Command("Y");
        return new SelfTestResult(int.Parse(response[1]));
    }

    /// <summary>
    /// Executes a baseline command. Actually no adjustment or measurement is performed.
    /// Only the internal measurement memory is deleted.
    /// </summary>
    public void Baseline()
    {
        string[] response = Command("G");
    }

    /// <summary>
    /// Checks whether the cuvette holder is empty.
    /// </summary>
    /// <returns>
    /// <c>true</c> if the cuvette holder is empty; otherwise, <c>false</c>.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown if the response value from the device cannot be parsed as an integer.
    /// </exception>
    /// <exception cref="IndexOutOfRangeException">
    /// Thrown if the device response does not contain the expected number of values.
    /// </exception>
    public bool IsCuvetteHolderEmpty()
    {
        string[] response = Command("X");
        return int.Parse(response[1]) == 1;
    }

    /// <summary>
    /// Performs an auto-gain operation at the specified level.
    /// Sends a command to the device and parses the response to determine if the operation was successful.
    /// </summary>
    /// <param name="level">The gain level (0-2500) to be set on the device.</param>
    /// <returns>An <see cref="AutoGainResult"/> indicating whether the gain was found and the LED power used.</returns>
    public AutoGainResult Autogain(int level)
    {
        string[] response = Command($"C {level}");

        if (int.Parse(response[1]) == 0)
        {
            return new AutoGainResult(false, int.Parse(response[2]));
        }
        else
        {
            return new AutoGainResult(true, int.Parse(response[2]));
        }
    }

    /// <summary>
    /// Performs a measurement and retrieves data from the device.
    /// </summary>
    /// <returns>
    /// A <see cref="SingleMeasurement"/> object containing the measured data for all channels.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown if any of the response values from the device cannot be parsed as integers.
    /// </exception>
    /// <exception cref="IndexOutOfRangeException">
    /// Thrown if the device response does not contain the expected number of values.
    /// </exception>
    public SingleMeasurement Measure()
    {
        string command = "M";

        string[] response = Command(command);
        return new SingleMeasurement(new Channel(double.Parse(response[1]), double.Parse(response[2]), int.Parse(response[3])));
    }

    /// <summary>
    /// Performs the first air measurement by measuring at minimum and maximum LED power levels.
    /// </summary>
    /// <returns>A <see cref="FirstAirMeasurementResult"/> containing the minimum and maximum measurements.</returns>
    public FirstAirMeasurementResult FirstAirMeasurement()
    {
        var powerMin = Get<int>(Index.CURRENT_LED470_POWER_MIN);
        var powerMax = Get<int>(Index.CURRENT_LED470_POWER_MAX);

        Set(Index.CURRENT_LED470_POWER, powerMin);
        var minMeasurement = Measure();

        Set(Index.CURRENT_LED470_POWER, powerMax);
        var maxMeasurement = Measure();

        return new FirstAirMeasurementResult(minMeasurement, maxMeasurement);
    }

    /// <summary>
    /// Performs the first sample measurement using an auto-gain operation to determine the optimal LED power level.
    /// </summary>
    /// <param name="factor">A scaling factor for determining the initial gain level.</param>
    /// <returns>A <see cref="FirstSampleMeasurementResult"/> containing the auto-gain result and the measurement.</returns>
    public FirstSampleMeasurementResult FirstSampleMeasurement(double factor = 0.8)
    {
        var autoGainResult = Autogain((int)(2500.0 * factor));
        var measurement = Measure();
        return new FirstSampleMeasurementResult(autoGainResult, measurement);
    }

    /// <summary>
    /// Verifies if the 2nd firmware image is valid.
    /// </summary>
    /// <returns>
    /// <c>true</c> if the verification was successful; otherwise, <c>false</c>.
    /// </returns>
    /// <exception cref="FormatException">
    /// Thrown if the response value from the device cannot be parsed as an integer.
    /// </exception>
    /// <exception cref="IndexOutOfRangeException">
    /// Thrown if the device response does not contain the expected number of values.
    /// </exception>
    public bool verify()
    {
        string[] response = Command("T");
        return int.Parse(response[1]) == 1;
    }

    /// <summary>
    /// Reboots the device.
    /// </summary>
    /// <remarks>
    /// After a restart, the unit may not respond for about 20 seconds.
    /// </remarks>
    private void reboot()
    {
        Command("R");
    }

    /// <summary>
    /// Erases the 2nd firmware image.
    /// The method sends the "F" command to the device, instructing it to erase stored data.
    /// </summary>
    private void erase()
    {
        Command("F");
    }

    /// <summary>
    /// Performs a firmware update on the device.
    /// The method reads the firmware file, erases the existing firmware, writes the new firmware line by line,
    /// and then verifies its validity. If the update fails at any stage, an exception is thrown.
    /// </summary>
    /// <param name="filename">
    /// The path to the firmware file that contains the new firmware image.
    /// </param>
    /// <exception cref="System.IO.IOException">
    /// Thrown if the firmware file cannot be read.
    /// </exception>
    /// <exception cref="Exception">
    /// Thrown if the firmware update fails at any stage (e.g., verification fails before or after reboot).
    /// </exception>
    /// <remarks>
    /// The update process follows these steps:
    /// 1. Read all lines from the specified firmware file.
    /// 2. Erase the existing firmware using <see cref="erase()"/>.
    /// 3. Send each line of the new firmware to the device using the "S {line}" command.
    /// 4. Verify the firmware using <see cref="verify()"/>; if verification fails, throw an exception.
    /// 5. Reboot the device and close the serial port.
    /// 6. Wait for 30 seconds to allow the device to restart.
    /// 7. Reopen the serial port and clear its buffers.
    /// 8. Verify the firmware again; if verification still passes, throw an exception indicating the update failed.
    /// </remarks>
    public void FwUpdate(string filename)
    {
        string[] fileLines = System.IO.File.ReadAllLines(filename);
        erase();
        foreach (string line in fileLines)
        {
            Command($"S {line}");
        }

        if (!verify())
        {
            throw new Exception($"Firmware update failed. Image not valid!");
        }

        reboot();
        serialPort_.Close();

        System.Threading.Thread.Sleep(30000); // Wait for 30 seconds

        serialPort_.Open();
        serialPort_.DiscardInBuffer();
        serialPort_.DiscardOutBuffer();

        if (verify())
        {
            throw new Exception($"Firmware update failed. Image still valid!");
        }
    }

    /// <summary>
    /// Generates a technical report containing various diagnostic data from the device.
    /// The report includes levelling results, self-test data, serial number, and firmware version.
    /// </summary>
    /// <returns>
    /// A <see cref="JsonNode"/> object containing structured diagnostic data.
    /// </returns>
    /// <remarks>
    /// The generated report consists of the following fields:
    /// - <see cref="Dict.LEVELLING"/>: The levelling results in JSON format.
    /// - <see cref="Dict.SELFTEST"/>: The base self-test results in JSON format, with additional details added via <see cref="AddSelfTestDetails"/>.
    /// - <see cref="Dict.SERIALNUMBER"/>: The device's serial number.
    /// - <see cref="Dict.FIRMWAREVERSION"/>: The firmware version currently installed on the device.
    /// - <see cref="Dict.PRODUCTIONNUMBER"/>: The device's production number.
    /// </remarks>
    public JsonNode TechnicalReport()
    {
        JsonObject obj = new JsonObject();

        obj[Dict.MEASURE] = FirstAirMeasurement().ToJson();
        obj[Dict.SELFTEST] = SelfTest().ToJson();
        obj[Dict.SERIALNUMBER] = SerialNumber();
        obj[Dict.FIRMWAREVERSION] = FirmwareVersion();
        obj[Dict.PRODUCTIONNUMBER] = ProductionNumber();

        return obj;
    }

    /// <summary>
    /// Returns a string representation of the device, including its serial port, serial number, and firmware version.
    /// </summary>
    /// <returns>
    /// A formatted string containing the device's port name, serial number, and firmware version.
    /// </returns>
    /// <remarks>
    /// The returned string follows the format:
    /// "eviFluor Module@{PortName} SN:{SerialNumber} Version:{FirmwareVersion}"
    /// Example output:
    /// "eviFluor Module@COM3 SN:12345678 Version:1.0.5"
    /// </remarks>
    public override string ToString()
    {
        var portName = "?";
        if (serialPort_ != null)
            portName = this.serialPort_.PortName;

        return $"eviFluor Module@{portName} SN:{serialNumber_} Version:{firmwareVersion_}";
    }

    /// <summary>
    /// Sets the status led color.
    /// </summary>
    /// <exception cref="IndexOutOfRangeException">
    /// Thrown if the device response does not contain the expected number of values.
    /// </exception>
    public void SetStatusLed(StatusLedColor color)
    {
        Command($"Z {(int)color}");
    }
}
using System;
using System.Collections.Generic;
using System.IO;
using System.IO.Ports;
using System.Linq;
using System.Management;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading.Tasks;

namespace Hse.EviFluor;

/// <summary>
/// Helper class to get eviFluor devices on Windows and Linux
/// </summary>
public static class DeviceFinder
{
    /// <summary>
    /// Retrieves a list of available eviFluor devices by scanning serial ports.    
    /// </summary>
    /// <returns>A list of serial numbers of available matching devices.</returns>
    public static List<string> GetAvailableDevices()
    {
        if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            return GetAvailableDevicesWindows();
        }
        else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
        {
            return GetAvailableDevicesLinux();
        }
        else
        {
            throw new Exception("OS not supported!");
        }
    }

    /// <summary>
    /// Finds the communication port associated with the given serial number.
    /// </summary>
    /// <param name="serialNumber">The device serial number (optional). If null, the first found device is returned.</param>
    /// <returns>The port name or device path if found; otherwise <c>null</c>.</returns>
    public static string? FindDevice(string? serialNumber)
    {
        if (RuntimeInformation.IsOSPlatform(OSPlatform.Windows))
        {
            return FindDeviceWindows(serialNumber);
        }
        else if (RuntimeInformation.IsOSPlatform(OSPlatform.Linux))
        {
            return FindDeviceLinux(serialNumber);
        }
        else
        {
            throw new Exception("OS not supported!");
        }
    }

    #region Linux Implementation

    /// <summary>
    /// Represents a USB serial device under Linux, identified by path and serial number.
    /// </summary>
    class Device : IEquatable<Device>
    {
        public string Path { get; }
        public string Sn { get; }

        public Device(string path, string sn)
        {
            this.Path = path;
            this.Sn = sn;
        }

        public override bool Equals(object? obj)
        {
            if (obj == null) return false;
            Device? objAsDevice = obj as Device;
            if (objAsDevice == null) return false;
            else return Equals(objAsDevice);
        }

        public bool Equals(Device? other)
        {
            if (other == null) return false;
            return this.Path == other.Path && this.Sn == other.Sn;
        }

        public override int GetHashCode()
        {
            return (Path.GetHashCode() ^ Sn.GetHashCode());
        }
    }

    /// <summary>
    /// Scans the Linux /sys USB hierarchy to collect connected devices matching the expected VID/PID.
    /// </summary>
    /// <returns>A list of detected <see cref="Device"/> instances.</returns>
    private static List<Device> GetAvailableDevicesInternal()
    {
        List<Device> devices = new List<Device>();
        ListDir("/sys/bus/usb/devices", 4, 0, ref devices);
        return devices;
    }

    /// <summary>
    /// Returns a list of serial numbers of all matching USB serial devices on Linux.
    /// </summary>
    private static List<string> GetAvailableDevicesLinux()
    {
        List<string> serialnumbers = new List<string>();

        foreach (Device d in GetAvailableDevicesInternal())
        {
            serialnumbers.Add(d.Sn);
        }

        return serialnumbers;
    }

    /// <summary>
    /// Finds the device path of a given serial number under Linux.
    /// </summary>
    /// <param name="serialNumber">Serial number to find (optional). If null, the first device is returned.</param>
    /// <returns>The device path (e.g., /dev/ttyUSB0) or null if not found.</returns>
    private static string? FindDeviceLinux(string? serialNumber)
    {
        string? portName = null;
        var devices = GetAvailableDevicesInternal();
        if (serialNumber == null)
        {
            if (devices.Count > 0)
            {
                portName = devices[0].Path;
            }
        }
        else
        {
            foreach (Device d in GetAvailableDevicesInternal())
            {
                if (d.Sn == serialNumber)
                {
                    portName = d.Path;
                    break;
                }
            }
        }

        return portName;
    }

    /// <summary>
    /// Finds the first TTY device file name in a directory.
    /// </summary>
    /// <param name="dirPath">Directory path to search.</param>
    /// <returns>TTY device name (e.g., ttyUSB0) or null if not found.</returns>
    private static string? FindTtyXXX(string dirPath)
    {
        if (!Directory.Exists(dirPath)) return null;

        foreach (var entry in Directory.EnumerateFileSystemEntries(dirPath))
        {
            string name = Path.GetFileName(entry);
            if (name == "." || name == "..") continue;
            return name;
        }
        return null;
    }

    /// <summary>
    /// Recursively searches for a "tty" subdirectory and extracts the TTY device name.
    /// </summary>
    /// <param name="dirPath">The base directory to start the search.</param>
    /// <param name="maxDepth">Maximum recursion depth.</param>
    /// <param name="currentDepth">Current recursion depth.</param>
    /// <returns>The found TTY name, or null if none found.</returns>
    private static string? FindTty(string dirPath, int maxDepth, int currentDepth)
    {
        if (currentDepth >= maxDepth || !Directory.Exists(dirPath)) return null;

        foreach (var entry in Directory.EnumerateFileSystemEntries(dirPath))
        {
            string name = Path.GetFileName(entry);
            if (name == "." || name == "..") continue;

            string path = Path.Combine(dirPath, name);

            if (name == "tty")
            {
                return FindTtyXXX(path);
            }

            var result = FindTty(path, maxDepth, currentDepth + 1);
            if (result != null) return result;
        }
        return null;
    }

    /// <summary>
    /// Reads the USB Vendor ID, Product ID, and Serial Number from sysfs entries.
    /// </summary>
    /// <param name="devPath">Path to the device directory in /sys/bus/usb/devices.</param>
    /// <returns>A tuple containing (vid, pid, serial) or null if not readable.</returns>
    private static (ushort vid, ushort pid, string sn)? GetDeviceVidPid(string devPath)
    {
        try
        {
            string vidPath = Path.Combine(devPath, "idVendor");
            string pidPath = Path.Combine(devPath, "idProduct");
            string snPath = Path.Combine(devPath, "serial");

            if (!File.Exists(vidPath) || !File.Exists(pidPath) || !File.Exists(pidPath)) return null;

            ushort vid = Convert.ToUInt16(File.ReadAllText(vidPath).Trim(), 16);
            ushort pid = Convert.ToUInt16(File.ReadAllText(pidPath).Trim(), 16);
            string sn = File.ReadAllText(snPath).Trim();

            return (vid, pid, sn);
        }
        catch { return null; }
    }

    /// <summary>
    /// Recursively traverses directories to detect USB devices matching VID/PID.
    /// </summary>
    /// <param name="dirPath">Starting directory (e.g., /sys/bus/usb/devices).</param>
    /// <param name="maxDepth">Maximum recursion depth.</param>
    /// <param name="currentDepth">Current recursion depth.</param>
    /// <param name="devices">Reference to a list to collect found devices.</param>
    private static void ListDir(string dirPath, int maxDepth, int currentDepth, ref List<Device> devices)
    {
        if (currentDepth >= maxDepth || !Directory.Exists(dirPath)) return;

        foreach (var entry in Directory.EnumerateFileSystemEntries(dirPath))
        {
            string name = Path.GetFileName(entry);
            if (name == "." || name == "..") continue;

            string path = Path.Combine(dirPath, name);

            var dev = GetDeviceVidPid(path);
            if (dev is { } ids)
            {
                var tty = FindTty(dirPath, 4, 0);
                if (ids.vid == USB.VID && ids.pid == USB.PID)
                {
                    if (tty != null)
                    {
                        var device = new Device("/dev/" + tty, ids.sn);
                        if (!devices.Contains(device))
                        {
                            devices.Add(device);
                        }
                    }
                }
            }

            ListDir(path, maxDepth, currentDepth + 1, ref devices);
        }
    }
    #endregion

    #region Windows Implementation
    /// <summary>
    /// Retrieves a list of available eviFluor devices by scanning serial ports.    
    /// </summary>
    /// <returns>A list of serial numbers of available matching devices.</returns>
    private static List<string> GetAvailableDevicesWindows()
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

    /// <summary>
    /// Extracts a 4-character hexadecimal value (e.g., VID or PID) from a PnP device ID.
    /// </summary>
    private static string ExtractValue(string deviceId, string key)
    {
        var startIndex = deviceId.IndexOf(key) + key.Length;
        return deviceId.Substring(startIndex, 4);
    }

    /// <summary>
    /// Retrieves the device serial number from a PNPDeviceID by returning its last path segment.
    /// </summary>
    private static string ExtractSerialNumber(string pnpDeviceId)
    {
        var parts = pnpDeviceId.Split('\\');
        if (parts.Length > 2)
        {
            return parts[^1];
        }
        return string.Empty;
    }

    /// <summary>
    /// Verifies that the given COM port corresponds to a device with the specified VID/PID
    /// and extracts its serial number via WMI.
    /// </summary>
    private static bool IsSerialPortMatchingVidAndPid(string portName, int vid, int pid, ref string serialNumber)
    {
        if (!OperatingSystem.IsWindows())
        {
            throw new PlatformNotSupportedException("This functionality is only supported on Windows.");
        }

        string vidAsHex = vid.ToString("X4");
        string pidAsHex = pid.ToString("X4");

        using var searcher = new ManagementObjectSearcher(@"SELECT * FROM Win32_PnPEntity WHERE Name LIKE '%(COM%'");
        foreach (var device in searcher.Get())
        {
            var name = device["Name"]?.ToString();
            var deviceId = device["DeviceID"]?.ToString();
            var pnpDeviceId = device["PNPDeviceID"]?.ToString();

            if (name != null && name.Contains($"({portName})") && deviceId != null && pnpDeviceId != null)
            {
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

    /// <summary>
    /// Finds the COM port for a device with the specified serial number.
    /// </summary>
    /// <param name="serialNumber">Serial number of the target device (optional).</param>
    /// <returns>The matching COM port (e.g., "COM3"), or null if not found.</returns>
    private static string? FindDeviceWindows(string? serialNumber)
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
    #endregion
}

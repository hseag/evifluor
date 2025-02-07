// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

using System;

namespace Hse.EviFluor;

/// <summary>
/// Provides USB-related constants.
/// </summary>
public static class USB
{
    /// <summary>
    /// Vendor ID (VID) of the USB device.
    /// </summary>
    public const int VID = 0x1CBE;

    /// <summary>
    /// Product ID (PID) of the USB device.
    /// </summary>
    public const int PID = 3;
}

/// <summary>
/// Defines constant dictionary keys used in measurement processing.
/// </summary>
public class Dict
{
    public const string COMMENT = "comment";
    public const string MEASUREMENTS = "measurements";
    public const string VALUES = "values";
    public const string RESULTS = "results";
    public const string SERIALNUMBER = "serialnumber";
    public const string FIRMWAREVERSION = "firmwareVersion";
    public const string SELFTEST = "selftest";
    public const string SELFTEST_RESULT = "result";
    public const string SELFTEST_COMUNICATION_ERROR = "comunicationerror";
    public const string VALUE = "value";
    public const string LED_POWER = "ledPower";
    public const string DARK = "dark";
    public const string CONCENTRATION = "concentration";
    public const string AIR = "air";
    public const string SAMPLE = "sample";
    public const string VALID = "valid";
    public const string MIN_MEASUREMENT = "min_measurement";
    public const string MAX_MEASUREMENT = "max_measurement";
    public const string MEASURE = "measure";
}

/// <summary>
/// Enumeration representing different index values for hardware configurations.
/// </summary>
public enum Index
{
    VERSION = 0,
    SERIALNUMBER = 1,
    HARDWARETYPE = 2,
    LAST_MEASUREMENT_COUNT = 10,
    AUTOGAIN_DELTA = 11,
    CUVETTE_EMPTY_DELTA = 12,
    CUVETTE_EMPTY_LED_POWER = 14,
    CURRENT_LED470_POWER = 15,
    CURRENT_LED470_POWER_MIN = 16,
    CURRENT_LED470_POWER_MAX = 17,
    CURRENT_LED625_POWER = 18,
    CURRENT_LED625_POWER_MIN = 19,
    CURRENT_LED625_POWER_MAX = 20
}

/// <summary>
/// Enumeration representing various error codes.
/// </summary>
public enum Error
{
    OK = 0,
    UNKNOWN_COMMAND = 1,
    INVALID_PARAMETER = 2,    
    SREC_FLASH_WRITE_ERROR = 4,
    SREC_UNSUPPORTED_TYPE = 5,
    SREC_INVALID_CRC = 6,
    SREC_INVALID_STRING = 7,
}

/// <summary>
/// Enumeration representing different data types.
/// </summary>
public enum TypeOf
{
    STRING = 0,
    UINT32 = 1,
    DOUBLE = 2
}


/// <summary>
/// Flags enumeration for self-test components.
/// </summary>
[Flags]
public enum Selftest
{
    COMUNICATION_ERROR = 0x00000001,
}
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
    /// <summary>
    /// JSON key 'comment'.
    /// </summary>
    public const string COMMENT = "comment";

    /// <summary>
    /// JSON key 'measurements'.
    /// </summary>
    public const string MEASUREMENTS = "measurements";

    /// <summary>
    /// JSON key 'values'.
    /// </summary>
    public const string VALUES = "values";

    /// <summary>
    /// JSON key 'results'.
    /// </summary>
    public const string RESULTS = "results";

    /// <summary>
    /// JSON key 'serialnumber'.
    /// </summary>
    public const string SERIALNUMBER = "serialnumber";

    /// <summary>
    /// JSON key 'firmwareVersion'.
    /// </summary>
    public const string FIRMWAREVERSION = "firmwareVersion";

    /// <summary>
    /// JSON key 'productionnumber'.
    /// </summary>
    public const string PRODUCTIONNUMBER = "productionnumber";

    /// <summary>
    /// JSON key 'selftest'.
    /// </summary>
    public const string SELFTEST = "selftest";

    /// <summary>
    /// JSON key 'result'.
    /// </summary>
    public const string SELFTEST_RESULT = "result";

    /// <summary>
    /// JSON key 'comunicationerror'.
    /// </summary>
    public const string SELFTEST_COMUNICATION_ERROR = "comunicationerror";

    /// <summary>
    /// JSON key 'value'.
    /// </summary>
    public const string VALUE = "value";

    /// <summary>
    /// JSON key 'ledPower'.
    /// </summary>
    public const string LED_POWER = "ledPower";

    /// <summary>
    /// JSON key 'dark'.
    /// </summary>
    public const string DARK = "dark";

    /// <summary>
    /// JSON key 'concentration'.
    /// </summary>
    public const string CONCENTRATION = "concentration";

    /// <summary>
    /// JSON key 'air'.
    /// </summary>
    public const string AIR = "air";

    /// <summary>
    /// JSON key 'sample'.
    /// </summary>
    public const string SAMPLE = "sample";

    /// <summary>
    /// JSON key 'valid'.
    /// </summary>
    public const string VALID = "valid";

    /// <summary>
    /// JSON key 'min_measurement'.
    /// </summary>
    public const string MIN_MEASUREMENT = "min_measurement";

    /// <summary>
    /// JSON key 'max_measurement'.
    /// </summary>
    public const string MAX_MEASUREMENT = "max_measurement";

    /// <summary>
    /// JSON key 'measure'.
    /// </summary>
    public const string MEASURE = "measure";

    /// <summary>
    /// JSON key 'logging'.
    /// </summary>
    public const string LOGGING = "logging";

    /// <summary>
    /// JSON key 'data_time'.
    /// </summary>
    public const string DATE_TIME = "date_time";

    /// <summary>
    /// JSON key 'errors'.
    /// </summary>
    public const string ERRORS = "errors";
}

/// <summary>
/// Enumeration representing different index values for hardware configurations.
/// </summary>
public enum Index
{
    /// <summary>
    /// Index for version.
    /// </summary>
    VERSION = 0,

    /// <summary>
    /// Index for serial number.
    /// </summary>
    SERIALNUMBER = 1,

    /// <summary>
    /// Index for production number.
    /// </summary>
    PRODUCTIONNUMBER = 3,

    /// <summary>
    /// Index for last measurement count.
    /// </summary>
    LAST_MEASUREMENT_COUNT = 10,

    /// <summary>
    /// Index for autogain delta.
    /// </summary>
    AUTOGAIN_DELTA = 11,

    /// <summary>
    /// Index for empty delta.
    /// </summary>
    CUVETTE_EMPTY_DELTA = 12,

    /// <summary>
    /// Index for empty cuvette guide led power.
    /// </summary>
    CUVETTE_EMPTY_LED_POWER = 14,

    /// <summary>
    /// Index for current led power (470 nm).
    /// </summary>
    CURRENT_LED470_POWER = 15,

    /// <summary>
    /// Index for minimal led power (470 nm).
    /// </summary>
    CURRENT_LED470_POWER_MIN = 16,

    /// <summary>
    /// Index for maximum led power (470 nm).
    /// </summary>
    CURRENT_LED470_POWER_MAX = 17,

    /// <summary>
    /// Index for current led power (625 nm).
    /// </summary>
    CURRENT_LED625_POWER = 18,

    /// <summary>
    /// Index for minimal led power (625 nm).
    /// </summary>
    CURRENT_LED625_POWER_MIN = 19,

    /// <summary>
    /// Index for maximum led power (625 nm).
    /// </summary>
    CURRENT_LED625_POWER_MAX = 20
}

/// <summary>
/// Enumeration representing various error codes.
/// </summary>
public enum Error
{
    /// <summary>
    /// No error.
    /// </summary>
    OK = 0,

    /// <summary>
    /// Unknown command.
    /// </summary>
    UNKNOWN_COMMAND = 1,

    /// <summary>
    /// Invalid parameter.
    /// </summary>
    INVALID_PARAMETER = 2,

    /// <summary>
    /// Flash write error.
    /// </summary>
    SREC_FLASH_WRITE_ERROR = 4,

    /// <summary>
    /// Unsupported SREC type.
    /// </summary>
    SREC_UNSUPPORTED_TYPE = 5,

    /// <summary>
    /// Invalid SREC crc.
    /// </summary>
    SREC_INVALID_CRC = 6,

    /// <summary>
    /// Invalid SREC string.
    /// </summary>
    SREC_INVALID_STRING = 7,
}

/// <summary>
/// Enumeration representing different data types.
/// </summary>
public enum TypeOf
{
    /// <summary>
    /// String type
    /// </summary>
    STRING = 0,

    /// <summary>
    /// Uint32 type
    /// </summary>
    UINT32 = 1,

    /// <summary>
    /// Double type
    /// </summary>
    DOUBLE = 2
}


/// <summary>
/// Flags enumeration for self-test components.
/// </summary>
[Flags]
public enum Selftest
{
    /// <summary>
    /// Indicates a communication error.
    /// </summary>
    COMUNICATION_ERROR = 0x00000001,
}

/// <summary>
/// Enumeration representing different status led colors .
/// </summary>
public enum StatusLedColor
{
    /// <summary>
    /// Status LED off.
    /// </summary>
    OFF = 0,

    /// <summary>
    /// Status LED red.
    /// </summary>
    RED = 1,

    /// <summary>
    /// Status LED green.
    /// </summary>
    GREEN = 2,

    /// <summary>
    /// Status LED blue.
    /// </summary>
    BLUE = 3,

    /// <summary>
    /// Status LED white.
    /// </summary>
    WHITE = 4,
}
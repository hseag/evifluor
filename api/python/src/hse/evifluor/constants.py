# SPDX-License-Identifier: MIT
# SPDX-FileCopyrightText: © 2025 HSE AG, <opensource@hseag.com>

from enum import IntEnum


class DictKeys:
    """Namespace for dictionary keys used throughout the module."""

    MEASUREMENTS                             = "measurements"
    SERIALNUMBER                             = "serialnumber"
    FIRMWAREVERSION                          = "firmwareVersion"
    PRODUCTIONNUMBER                         = "productionnumber"
    VALUES                                   = "values"
    VALUE                                    = "value"
    LED_POWER                                = "ledPower"
    DARK                                     = "dark"
    COMMENT                                  = "comment"
    RESULTS                                  = "results"
    CONCENTRATION                            = "concentration"
    RFU                                      = "rfu"
    AIR                                      = "air"
    SAMPLE                                   = "sample"
    VALID                                    = "valid"
    CH_470                                   = "470"
    CH_625                                   = "625"
    SELFTEST                                 = "selftest"
    SELFTEST_RESULT                          = "result"
    SELFTEST_COMUNICATION_ERROR              = "comunicationerror"
    MIN_MEASUREMENT                          = "min_measurement"
    MAX_MEASUREMENT                          = "max_measurement"
    MEASURE                                  = "measure"
    AIR_DARK                                 = f"{AIR} {DARK}"
    AIR_VALUE                                = f"{AIR} {VALUE}"
    AIR_LED_POWER                            = f"{AIR} {LED_POWER}"
    SAMPLE_DARK                              = f"{SAMPLE} {DARK}"
    SAMPLE_VALUE                             = f"{SAMPLE} {VALUE}"
    SAMPLE_LED_POWER                         = f"{SAMPLE} {LED_POWER}"
    INFO                                     = "info"
    LOGGING                                  = "logging"
    ERRORS                                   = "errors"
    DATE_TIME                                = "date_time"
    AUTOGAIN_RESULT_FOUND                    = "found"
    AUTOGAIN_RESULT_LED_POWER                = "led_power"

class USB(IntEnum):
    VID                                           = 7358
    PID                                           = 3

class Index(IntEnum):
    VERSION                                       = 0
    SERIALNUMBER                                  = 1
    PRODUCTIONNUMBER                              = 3
    LAST_MEASUREMENT_COUNT                        = 10
    AUTOGAIN_DELTA                                = 11
    CUVETTE_EMPTY_DELTA                           = 12
    CUVETTE_EMPTY_LED_POWER                       = 14
    CURRENT_LED470_POWER                          = 15
    CURRENT_LED470_POWER_MIN                      = 16
    CURRENT_LED470_POWER_MAX                      = 17
    CURRENT_LED625_POWER                          = 18
    CURRENT_LED625_POWER_MIN                      = 19
    CURRENT_LED625_POWER_MAX                      = 20


class Error(IntEnum):
    OK                                            = 0
    UNKNOWN_COMMAND                               = 1
    INVALID_PARAMETER                             = 2
    TIMEOUT                                       = 3
    SREC_FLASH_WRITE_ERROR                        = 4
    SREC_UNSUPPORTED_TYPE                         = 5
    SREC_INVALID_CRC                              = 6
    SREC_INVALID_STRING                           = 7

class TypeOf(IntEnum):                            
    STRING                                        = 0
    UINT32                                        = 1
    DOUBLE                                        = 2
    
class Selftest(IntEnum):
    COMUNICATION_ERROR                            = 0x00000001
    
class Color(IntEnum):                            
    OFF   = 0
    RED   = 1
    GREEN = 2
    BLUE  = 3
    WHITE = 4

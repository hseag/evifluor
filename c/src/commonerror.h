/*
 * Copyright (C) 2025 Hombrechtikon Systems Engineering AG
 */

#pragma once

#include "stdint.h"

typedef uint16_t Error;

typedef enum Errors
{                                                         //| FIW | R&D | C-SWI |
    ERROR_EVI_OK                                    = 0,  //|  x  |  x  |  x    |
    ERROR_EVI_UNKNOWN_COMMAND                       = 1,  //|  x  |  -  |  -    |
    ERROR_EVI_INVALID_PARAMETER                     = 2,  //|  x  |  -  |  -    |
    ERROR_EVI_TIMEOUT                               = 3,  //|  -  |  x  |  -    |
    ERROR_EVI_SREC_FLASH_WRITE_ERROR                = 4,  //|  x  |  -  |  -    |
    ERROR_EVI_SREC_UNSUPPORTED_TYPE                 = 5,  //|  x  |  -  |  -    |
    ERROR_EVI_SREC_INVALID_CRC                      = 6,  //|  x  |  -  |  -    |
    ERROR_EVI_SREC_INVALID_STRING                   = 7,  //|  x  |  -  |  -    |
    ERROR_EVI_FILE_NOT_FOUND                        = 8,  //|  -  |  -  |  x    |
    ERROR_EVI_PROGRAMMING_FAILED                    = 9,  //|  -  |  x  |  -    |
    ERROR_EVI_INSTRUMENT_NOT_FOUND                  = 10, //|  -  |  -  |  x    |
    ERROR_EVI_NO_MORE_LOGGING                       = 11, //|  x  |  -  |  -    |
    ERROR_EVI_UNKOWN_COMMAND_LINE_OPTION            = 50, //|  -  |  -  |  x    |
    ERROR_EVI_RESPONSE_ERROR                        = 51, //|  -  |  -  |  x    |
    ERROR_EVI_PROTOCOL_ERROR                        = 52, //|  -  |  -  |  x    |
    ERROR_EVI_UNKOWN_COMMAND_LINE_ARGUMENT          = 53, //|  -  |  -  |  x    |
    ERROR_EVI_INVALID_NUMBER                        = 55, //|  -  |  -  |  x    |
    ERROR_EVI_FILE_IO_ERROR                         = 56, //|  -  |  -  |  x    |
    
    ERROR_EVI_USER                                  = 100,//|     |     |       |
} Error_t;

// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "printerror.h"
#include <stdio.h>

Error_t printError(Error_t error, char * format, ...)
{
    if(format)
    {
      va_list args;
      fprintf_s(stderr, "Error (%i): \n", error);
      va_start(args, format);
      vfprintf(stderr, format, args);
      va_end(args);
    }
    else
    {
      fprintf_s(stderr, "Error (%i): %s\n", error, eviError2String(error));
    }
    return error;
}

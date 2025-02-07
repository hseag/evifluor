// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdset.h"
#include "printerror.h"
#include <stdlib.h>
#include <stdio.h>

Error_t cmdSet(Evi_t *self, const char *sIndex, const char *sValue)
{
    char *endptr;
    long index = strtol(sIndex, &endptr, 10);
    Error_t ret;

    if (*endptr == '\0')
    {
        ret = eviSet(self, index, sValue);

        if (ret != ERROR_EVI_OK)
        {
            printError(ret, NULL);
        }
    }
    else
    {
        ret = ERROR_EVI_INVALID_NUMBER;
        printError(ret, "'%s' is not a valid number.", sIndex);
    }
    return ret;
}

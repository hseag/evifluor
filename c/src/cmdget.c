// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdget.h"
#include "printerror.h"
#include <stdlib.h>
#include <stdio.h>

Error_t cmdGet(Evi_t *self, const char *sIndex)
{
    char value[EVI_MAX_LINE_LENGTH];
    uint32_t valueSize = EVI_MAX_LINE_LENGTH;
    char *endptr;
    long index = strtol(sIndex, &endptr, 10);

    Error_t ret;

    if (*endptr == '\0')
    {
        ret = eviGet(self, index, value, valueSize);

        if (ret == ERROR_EVI_OK)
        {
            fprintf_s(stdout, "%s\n", value);
        }
        else
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

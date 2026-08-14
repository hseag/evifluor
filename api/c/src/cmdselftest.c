// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdselftest.h"
#include "printerror.h"
#include <stdlib.h>
#include <stdio.h>

Error_t cmdSelftest(Evi_t *self)
{
    uint32_t result = 0;
    Error_t ret;

    ret = eviSelftest(self, &result);

    if (ret == ERROR_EVI_OK)
    {
        if(result == 0)
        {
            fprintf_s(stdout, "Selftest passed.\n");
        }
        else
        {
            fprintf_s(stdout, "Selftest failed:\n");
        }
    }
    else
    {
        printError(ret, NULL);
    }
    return ret;
}

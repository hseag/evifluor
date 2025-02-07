// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdbaseline.h"
#include "printerror.h"
#include <stdlib.h>
#include <stdio.h>

Error_t cmdBaseline(Evi_t * self)
{
    Error_t ret = eviFluorBaseline(self);
    if (ret == ERROR_EVI_OK)
    {
    }
    else
    {
        printError(ret, NULL);
    }
    return ret;
}

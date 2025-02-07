// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdempty.h"
#include "evifluor.h"
#include "printerror.h"
#include <stdlib.h>
#include <stdio.h>

Error_t cmdEmpty(Evi_t *self)
{
    bool empty = 0;
    Error_t ret;

    ret = eviFluorIsCuvetteHolderEmpty(self, &empty);

    if (ret == ERROR_EVI_OK)
    {
        if(empty)
        {
            fprintf_s(stdout, "Empty\n");
        }
        else
        {
            fprintf_s(stdout, "Not empty\n");
        }
    }
    else
    {
        printError(ret, NULL);
    }
    return ret;
}

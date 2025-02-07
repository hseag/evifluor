// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdfwupdate.h"
#include "printerror.h"
#include <stdlib.h>
#include <stdio.h>

Error_t cmdFwUpdate(Evi_t *self, const char * file)
{
    Error_t ret;
    ret = eviFwUpdate(self, file);

    if (ret != ERROR_EVI_OK)
    {
        printError(ret, NULL);
    }
    return ret;
}

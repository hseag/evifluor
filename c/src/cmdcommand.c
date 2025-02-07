// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdcommand.h"
#include "printerror.h"
#include <stdlib.h>
#include <stdio.h>

Error_t cmdCommand(Evi_t * self, const char * command)
{
    EvieResponse_t * response = eviCreateResponse();
    Error_t ret = eviCommand(self, command, response);

    if (ret == ERROR_EVI_OK)
    {
        for(uint32_t i=0; i<response->argc; i++)
        {
            fprintf_s(stdout, "%s%s", i==0 ? "":" ", response->argv[i]);
        }
        fprintf_s(stdout, "\n");
        
    }
    else
    {
        printError(ret, NULL);
    }

    eviFreeResponse(response);
    return ret;
}

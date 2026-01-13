// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmddata.h"
#include "cJSON.h"
#include "dict.h"
#include "printerror.h"
#include "measurement.h"
#include "singlemeasurement.h"
#include "json.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

static Error_t cmdCalculate(Evi_t *self, int argcCmd, char **argvCmd)
{
    Error_t ret = ERROR_EVI_OK;
    int argcCmdSave = argcCmd;
    char **argvCmdSave = argvCmd;

    bool options = true;
    int i = 0;

    while (i < argcCmd && options)
    {
        if (strncmp(argvCmd[i], "--", 2) == 0 || strncmp(argvCmd[i], "-", 1) == 0)
        {
            i++;
        }
        else
        {
            options = false;
        }
    }

    argcCmdSave = argcCmd - i;
    argvCmdSave = argvCmd + i;

    if (argcCmdSave == 5)
    {
        char *file = argvCmdSave[4];
        cJSON *json = json_loadFromFile(file);

        double concentrationLow = atof(argvCmdSave[0]);
        double concentrationHigh = atof(argvCmdSave[1]);
        int nrOfStdLow = atoi(argvCmdSave[2]);
        int nrOfStdHigh = atoi(argvCmdSave[3]);

        if (json != NULL)
        {
            cJSON *oMeasurements = cJSON_GetObjectItem(json, DICT_MEASUREMENTS);

            measurement_calculate(oMeasurements, concentrationLow, concentrationHigh, nrOfStdLow, nrOfStdHigh);
            json_saveToFile(file, json);

            cJSON_Delete(json);
        }
        else
        {
            ret = ERROR_EVI_FILE_NOT_FOUND;
            printError(ret, "File %s not found.", file);
        }
    }
    else
    {
        ret = ERROR_EVI_INVALID_PARAMETER;
        printError(ret, "Wrong number of parameters. Expected 5, given %d.", argcCmdSave);
    }
    return ret;
}

static Error_t cmdDataPrint(Evi_t *self, char *file)
{
    cJSON *json = json_loadFromFile(file);

    if (json != NULL)
    {
        cJSON *oMeasurments = cJSON_GetObjectItem(json, DICT_MEASUREMENTS);
        if (oMeasurments)
        {
            cJSON *iterator = NULL;
            cJSON_ArrayForEach(iterator, oMeasurments)
            {
                cJSON *oCalculated = cJSON_GetObjectItem(iterator, DICT_CALCULATED);
                cJSON *oComment = cJSON_GetObjectItem(iterator, DICT_COMMENT);
                if (oCalculated)
                {
                    cJSON *oConcentration = cJSON_GetObjectItem(oCalculated, DICT_CONCENTRATION);
                    if (oConcentration)
                    {
                        fprintf_s(stdout, "%f ", cJSON_GetNumberValue(oConcentration));
                    }

                    if (oComment)
                    {
                        fprintf_s(stdout, "%s ", cJSON_GetStringValue(oComment));
                    }
                    fprintf_s(stdout, "\n");
                }
            }
        }
        cJSON_Delete(json);
        return ERROR_EVI_OK;
    }
    else
    {
        printError(ERROR_EVI_FILE_NOT_FOUND, "File %s not found.", file);
        return ERROR_EVI_FILE_NOT_FOUND;
    }
}

Error_t cmdData(Evi_t *self, int argcCmd, char **argvCmd)
{
    Error_t ret = ERROR_EVI_OK;

    if ((argcCmd >= 5) && (strcmp(argvCmd[1], "calculate") == 0))
    {
        ret = cmdCalculate(self, argcCmd - 2, argvCmd + 2);
    }
    else if ((argcCmd == 3) && (strcmp(argvCmd[1], "print") == 0))
    {
        ret = cmdDataPrint(self, argvCmd[2]);
    }
    else
    {
        ret = ERROR_EVI_INVALID_PARAMETER;
    }

    if (ret != ERROR_EVI_OK)
    {
        printError(ret, NULL);
    }

    return ret;
}

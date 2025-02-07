// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmddata.h"
#include "cJSON.h"
#include "printerror.h"
#include "measurement.h"
#include "json.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

SingleMeasurement_t singleMeasurementFromJson(cJSON *obj, bool * valid)
{
    SingleMeasurement_t ret = {0};

    cJSON *oDark = cJSON_GetObjectItem(obj, DICT_DARK);
    cJSON *oValue = cJSON_GetObjectItem(obj, DICT_VALUE);
    cJSON *oLedPower = cJSON_GetObjectItem(obj, DICT_LED_POWER);

    if(oDark && oValue && oLedPower)
    {
        ret = singleMeasurement_init(channel_init(cJSON_GetNumberValue(oDark), cJSON_GetNumberValue(oValue), cJSON_GetNumberValue(oLedPower)));
        *valid = true;
    }
    else
    {
        *valid = false;
    }

    return ret;
}

Measurement_t measurementFromJson(cJSON * obj, bool * valid)
{
    Measurement_t ret = {0};

    cJSON* oAir = cJSON_GetObjectItem(obj, DICT_AIR);
    cJSON* oSample = cJSON_GetObjectItem(obj, DICT_SAMPLE);
    if(oAir && oSample)
    {
        bool validAir;
        bool validSample;
        ret = measurement_init(singleMeasurementFromJson(oAir, &validAir), singleMeasurementFromJson(oSample, &validSample));
        *valid = validAir && validSample;
    }
    else
    {
        *valid = false;
    }

    return ret;
}

static cJSON *calculate(cJSON *obj, Factors_t * factors)
{
    cJSON *ret = cJSON_CreateObject();
    bool valid;

    Measurement_t measurement = measurementFromJson(obj, &valid);

    if(valid)
    {
        double concentration = measurement_concentration(&measurement, factors);

        cJSON_AddNumberToObject(ret, DICT_CONCENTRATION, concentration);
    }

    return ret;
}

static bool getSupportPoint(cJSON* oMeasurments, uint32_t index, Measurement_t * s)
{
    bool ret = false;

    if (index < cJSON_GetArraySize(oMeasurments))
    {
        cJSON* measurement = cJSON_GetArrayItem(oMeasurments, index);
        if (measurement)
        {
            bool valid;
            *s = measurementFromJson(measurement, &valid);
            if(valid)
            {
                ret = true;
            }
            else
            {
                cJSON* values = cJSON_GetObjectItem(measurement, DICT_VALUES);
                if (values && cJSON_GetArraySize(values) == 3)
                {
                    SingleMeasurement_t minMeasurement = {0};
                    SingleMeasurement_t maxMeasurement = {0};

                    cJSON* oMin    = cJSON_GetArrayItem(values, 0);
                    cJSON* oMax    = cJSON_GetArrayItem(values, 1);
                    cJSON* oSample = cJSON_GetArrayItem(values, 2);

                    if(oMin && oMax && oSample)
                    {
                        bool valid1;
                        bool valid2;
                        bool valid3;
                        s->sample = singleMeasurementFromJson(oSample, &valid1);
                        minMeasurement        = singleMeasurementFromJson(oMin, &valid2);
                        maxMeasurement        = singleMeasurementFromJson(oMax, &valid3);

                        if(valid1 && valid2 && valid3)
                        {
                          s->air = eviFluorAdjustToLedPower(&minMeasurement, &maxMeasurement, s->sample.channel470.ledPower);

                          cJSON_AddItemToObject(measurement, DICT_AIR, singleMeasurmentToJson(&(s->air)));
                          cJSON_AddItemToObject(measurement, DICT_SAMPLE, singleMeasurmentToJson(&(s->sample)));

                          ret = true;
                        }
                    }
                }
            }
        }
    }
    return ret;
}

static Error_t cmdCalculate(Evi_t *self, int argcCmd, char **argvCmd)
{
    Error_t ret = ERROR_EVI_OK;
    int argcCmdSave = argcCmd;
    char **argvCmdSave = argvCmd;

    Measurement_t stdLow = {0};
    Measurement_t stdHigh = {0};

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

    if (argcCmdSave == 3)
    {
        char *file = argvCmdSave[2];
        cJSON *json = jsonLoad(file);

        double concentrationLow = atof(argvCmdSave[0]);
        double concentrationHigh = atof(argvCmdSave[1]);

        if (json != NULL)
        {
            cJSON *oMeasurments = cJSON_GetObjectItem(json, DICT_MEASUREMENTS);

            if (oMeasurments)
            {
                if(getSupportPoint(oMeasurments, 0, &stdHigh) && getSupportPoint(oMeasurments, 1, &stdLow))
                {

                    Factors_t factors = measurement_calculateFactors(concentrationLow, concentrationHigh, &stdLow, &stdHigh);
                    {
                        cJSON *iterator = NULL;
                        cJSON_ArrayForEach(iterator, oMeasurments)
                        {
                            cJSON_DeleteItemFromObject(iterator, DICT_CALCULATED);
                            cJSON_AddItemToObject(iterator, DICT_CALCULATED, calculate(iterator, &factors));
                        }
                    }
                }
                else 
                {
                    ret = ERROR_EVI_INVALID_PARAMETER;
                }
            }

            jsonSave(file, json);

            cJSON_Delete(json);
        }
        else
        {
            ret = ERROR_EVI_FILE_NOT_FOUND;
            printError(ret, "File %s not found.", file);
        }
    }
    return ret;
}

static Error_t cmdDataPrint(Evi_t *self, char *file)
{
    cJSON *json = jsonLoad(file);

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

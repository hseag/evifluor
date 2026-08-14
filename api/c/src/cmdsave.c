// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdsave.h"
#include "commonindex.h"
#include "evifluorindex.h"
#include "cJSON.h"
#include "json.h"
#include "dict.h"
#include "printerror.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>

typedef struct
{
    bool append;
    bool raw;
    char * filename;
    char * comment;
} Options_t;

static cJSON * singleMeasurement(Evi_t* self, int index)
{
    Error_t  ret = ERROR_EVI_OK;
    SingleMeasurement_t measurement;

    ret = eviFluorLastMeasurements(self, index, &measurement);
    if (ret == ERROR_EVI_OK)
    {
        return singleMeasurement_toJson(&measurement);
    }
    else
    {
        printError(ret, "Could not read measurement");
        return NULL;
    }
}

static Error_t addMeasurement(Evi_t* self, Options_t * options, cJSON* json)
{
    Error_t ret = ERROR_EVI_OK;
    char    value[20];

    cJSON* oMeasurements = cJSON_GetObjectItem(json, DICT_MEASUREMENTS);

    cJSON* obj = cJSON_CreateObject();

    if (options->comment != NULL)
    {
        cJSON_AddItemToObject(obj, DICT_COMMENT, cJSON_CreateString(options->comment));
    }

    ret = eviGet(self, INDEX_LASTMEASUREMENTCOUNT, value, sizeof(value));
    if (ret != ERROR_EVI_OK)
    {
        printError(ret, "Could not read measurement count");
        return ret;
    }

    int lastMeasurementsCount = atoi(value);

    if(lastMeasurementsCount == 2 && options->raw == false)
    {
        cJSON_AddItemToObject(obj, DICT_AIR, singleMeasurement(self, 1));
        cJSON_AddItemToObject(obj, DICT_SAMPLE, singleMeasurement(self, 0));
    }
    else
    {
        cJSON* arr = cJSON_CreateArray();
        for(int i = lastMeasurementsCount-1; i>=0; i--)
        {
            cJSON_AddItemToArray(arr, singleMeasurement(self, i));
        }
        cJSON_AddItemToObject(obj, DICT_VALUES, arr);
    }
    cJSON_AddItemToArray(oMeasurements, obj);

    return ERROR_EVI_OK;
}

cJSON* dataLoadJson(Evi_t* self, const char * filename, bool append)
{
    cJSON* json = NULL;

    if(append == true)
    {
        json = json_loadFromFile(filename);
    }

    // create new JSON file
    if (json == NULL)
    {
        Error_t ret = ERROR_EVI_OK;
        char    value[100];

        json = cJSON_CreateObject();

        ret = eviGet(self, INDEX_SERIALNUMBER, value, sizeof(value));
        if (ret == ERROR_EVI_OK)
        {
            cJSON_AddItemToObject(json, DICT_SERIALNUMBER, cJSON_CreateString(value));
        }

        ret = eviGet(self, INDEX_VERSION, value, sizeof(value));
        if (ret == ERROR_EVI_OK)
        {
            cJSON_AddItemToObject(json, DICT_FIRMWAREVERSION, cJSON_CreateString(value));
        }

        cJSON_AddItemToObject(json, DICT_MEASUREMENTS, cJSON_CreateArray());
    }

    return json;
}

Error_t cmdSave(Evi_t* self, int argcCmd, char** argvCmd)
{
    cJSON*  json = NULL;
    Error_t ret  = ERROR_EVI_OK;

    Options_t options = { 0 };

    options.append = true;
    options.raw    = false;

    int argcCmdSave = argcCmd;
    char **argvCmdSave = argvCmd;
    bool parsingOptions = true;
    size_t i = 1;

    while (i < argcCmd && parsingOptions)
    {
        if (strncmp(argvCmd[i], "--", 2) == 0 || strncmp(argvCmd[i], "-", 1) == 0)
        {
            if (strcmp(argvCmd[i], "--append") == 0)
            {
                options.append = true;
            }
            else if (strcmp(argvCmd[i], "--create") == 0)
            {
                options.append = false;
            }
            else if (strcmp(argvCmd[i], "--mode-raw") == 0)
            {
                options.raw = true;
            }
            else if (strcmp(argvCmd[i], "--mode-measurement") == 0)
            {
                options.raw = false;
            }
            else
            {
                ret = printError(ERROR_EVI_UNKOWN_COMMAND_LINE_OPTION, "Unknown option: %s\n", argvCmd[i]);
                goto exit;
            }
            i++;
        }
        else
        {
            parsingOptions = false;
        }
    }

    argcCmdSave = argcCmd - i;
    argvCmdSave = argvCmd + i;

    if(argcCmdSave == 1)
    {
        options.filename = strdup(argvCmdSave[0]);
    }
    else if(argcCmdSave == 2)
    {
        options.filename = strdup(argvCmdSave[0]);
        options.comment  = strdup(argvCmdSave[1]);
    }
    else
    {
        ret = printError(ERROR_EVI_UNKOWN_COMMAND_LINE_ARGUMENT, NULL);
        goto exit;
    }

    json = dataLoadJson(self, options.filename, options.append);
    ret  = addMeasurement(self, &options, json);
    if (ret == ERROR_EVI_OK)
    {
        json_saveToFile(options.filename, json);
    }
exit:
    if (json)
        cJSON_Delete(json);
    free(options.filename);
    free(options.comment);

    return ret;
}

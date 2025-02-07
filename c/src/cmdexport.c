// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdexport.h"
#include "json.h"
#include "evifluor.h"
#include "printerror.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>

typedef enum
{
    MODE_RAW,
    MODE_MEASUREMENT
} Mode_t;

typedef struct
{
    char delimiter;
    char * filenameJson;
    char * filenameCsv;
    Mode_t mode;
} Options_t;

void exportRawMeasurement(Options_t * options, cJSON *object, FILE * csv, bool last)
{
    if(object)
    {
        cJSON * dark     = cJSON_GetObjectItem(object, DICT_DARK);
        cJSON * value    = cJSON_GetObjectItem(object, DICT_VALUE);
        cJSON * ledPower = cJSON_GetObjectItem(object, DICT_LED_POWER);

        fprintf_s(csv, "%f%c", dark ? cJSON_GetNumberValue(dark) : 0, options->delimiter);
        fprintf_s(csv, "%f%c", value ? cJSON_GetNumberValue(value) : 0, options->delimiter);
        fprintf_s(csv, "%d", value ? (int)cJSON_GetNumberValue(ledPower) : 0);
        if(!last)
        {
            fprintf_s(csv, "%c", options->delimiter);
        }
    }
}

void exportRaw(Options_t * options, cJSON *object, FILE * csv)
{
    cJSON *iterator = NULL;
    cJSON *oComment = cJSON_GetObjectItem(object, DICT_COMMENT);

    fprintf_s(csv, "%s%c", oComment ? cJSON_GetStringValue(oComment) : "", options->delimiter);

    cJSON *oValues = cJSON_GetObjectItem(object, DICT_VALUES);
    bool first = true;

    cJSON_ArrayForEach(iterator, oValues)
    {
        if(!first)
        {
            fprintf_s(csv, "%s%c", oComment ? cJSON_GetStringValue(oComment) : "", options->delimiter);
        }

        exportRawMeasurement(options, iterator, csv, true);
        fprintf_s(csv, "\n");
        first = false;
    }
}

void exportMeasurement(Options_t * options, cJSON *object, FILE * csv)
{
    cJSON *oComment = cJSON_GetObjectItem(object, DICT_COMMENT);

    cJSON *oAir = cJSON_GetObjectItem(object, DICT_AIR);
    cJSON *oSample = cJSON_GetObjectItem(object, DICT_SAMPLE);

    if(oAir != NULL && oSample != NULL)
    {
        fprintf_s(csv, "%s%c", oComment ? cJSON_GetStringValue(oComment) : "", options->delimiter);
        exportRawMeasurement(options, oAir, csv, false);
        exportRawMeasurement(options, oSample, csv, true);
        fprintf_s(csv, "\n");
    }
}

void exportRawHeader(Options_t * options, FILE * csv)
{
    fprintf_s(csv, "%s%c", DICT_COMMENT, options->delimiter);
    fprintf_s(csv, "%s%c", DICT_DARK, options->delimiter);
    fprintf_s(csv, "%s%c", DICT_VALUE, options->delimiter);
    fprintf_s(csv, "%s", DICT_LED_POWER);
    fprintf_s(csv, "\n");
}

void exportMeasurementHeader(Options_t * options, FILE * csv)
{
    fprintf_s(csv, "%s%c", DICT_COMMENT, options->delimiter);
    fprintf_s(csv, "%s%c", DICT_AIR_DARK, options->delimiter);
    fprintf_s(csv, "%s%c", DICT_AIR_VALUE, options->delimiter);
    fprintf_s(csv, "%s%c", DICT_AIR_LED_POWER, options->delimiter);
    fprintf_s(csv, "%s%c", DICT_SAMPLE_DARK, options->delimiter);
    fprintf_s(csv, "%s%c", DICT_SAMPLE_VALUE, options->delimiter);
    fprintf_s(csv, "%s",   DICT_SAMPLE_LED_POWER);
    fprintf_s(csv, "\n");
}

static Error_t export(Options_t * options)
{
    Error_t ret  = ERROR_EVI_OK;
    cJSON* json = jsonLoad(options->filenameJson);

    if(json)
    {
        FILE * csv = fopen(options->filenameCsv, "w");
        if(csv)
        {
            cJSON *oMeasurments = cJSON_GetObjectItem(json, DICT_MEASUREMENTS);
            cJSON *iterator = NULL;
            switch(options->mode)
            {
                case MODE_RAW:
                    exportRawHeader(options, csv);
                    break;
                case MODE_MEASUREMENT:
                    exportMeasurementHeader(options, csv);
                    break;
            }

            cJSON_ArrayForEach(iterator, oMeasurments)
            {
                switch(options->mode)
                {
                    case MODE_RAW:
                        exportRaw(options, iterator, csv);
                        break;
                    case MODE_MEASUREMENT:
                        exportMeasurement(options, iterator, csv);
                        break;
                }

            }
            fclose(csv);
        }
        else
        {
            ret = ERROR_EVI_FILE_IO_ERROR;
        }
        cJSON_Delete(json);
    }
    else
    {
        ret = ERROR_EVI_FILE_NOT_FOUND;
    }
    return ret;
}


Error_t cmdExport(Evi_t* self, int argcCmd, char** argvCmd)
{
    Error_t ret  = ERROR_EVI_OK;
    Options_t options = { 0 };

    options.delimiter = ',';
    options.mode      = MODE_MEASUREMENT;

    int argcCmdSave = argcCmd;
    char **argvCmdSave = argvCmd;
    bool parsingOptions = true;
    size_t i = 1;
    
    while (i < argcCmd && parsingOptions)
    {
        if (strncmp(argvCmd[i], "--", 2) == 0 || strncmp(argvCmd[i], "-", 1) == 0)
        {
            if (strcmp(argvCmd[i], "--delimiter-comma") == 0)
            {
                options.delimiter  = ',';
            }
            else if (strcmp(argvCmd[i], "--delimiter-semicolon") == 0)
            {
                options.delimiter  = ';';
            }
            else if (strcmp(argvCmd[i], "--delimiter-tab") == 0)
            {
                options.delimiter  = '\t';
            }
            else if (strcmp(argvCmd[i], "--mode-raw") == 0)
            {
                options.mode  = MODE_RAW;
            }
            else if (strcmp(argvCmd[i], "--mode-measurement") == 0)
            {
                options.mode  = MODE_MEASUREMENT;
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

    if(argcCmdSave == 2)
    {
        options.filenameJson = strdup(argvCmdSave[0]);
        options.filenameCsv  = strdup(argvCmdSave[1]);
    }
    else
    {
        ret = printError(ERROR_EVI_UNKOWN_COMMAND_LINE_ARGUMENT, NULL);
        goto exit;
    }

    ret = export(&options);



exit:

    free(options.filenameJson);
    free(options.filenameCsv);

    return ret;
}

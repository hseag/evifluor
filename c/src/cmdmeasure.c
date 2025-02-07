// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "cmdmeasure.h"
#include "printerror.h"
#include <stdlib.h>
#include <stdio.h>

typedef enum
{
    MEASUREMENT_TYPE_MEASURE,
    MEASUREMENT_TYPE_FIRST_AIR,
    MEASUREMENT_TYPE_FIRST_SAMPLE,
} MeasurementType_t;

typedef struct
{
    MeasurementType_t measurementType;
} Options_t;

Error_t cmdMeasure(Evi_t * self, int argcCmd, char** argvCmd)
{
    Error_t ret  = ERROR_EVI_OK;
    Options_t options = { 0 };

    options.measurementType = MEASUREMENT_TYPE_MEASURE;

    bool parsingOptions = true;
    size_t i = 1;

    while (i < argcCmd && parsingOptions)
    {
        if (strncmp(argvCmd[i], "--", 2) == 0 || strncmp(argvCmd[i], "-", 1) == 0)
        {
            if (strcmp(argvCmd[i], "--measure") == 0)
            {
                options.measurementType = MEASUREMENT_TYPE_MEASURE;
            }
            else if (strcmp(argvCmd[i], "--first-air") == 0)
            {
                options.measurementType = MEASUREMENT_TYPE_FIRST_AIR;
            }
            else if (strcmp(argvCmd[i], "--first-sample") == 0)
            {
                options.measurementType = MEASUREMENT_TYPE_FIRST_SAMPLE;
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

    switch(options.measurementType)
    {
        case MEASUREMENT_TYPE_MEASURE:
        {
            SingleMeasurement_t measurement;
            ret = eviFluorMeasure(self, &measurement);
            if (ret == ERROR_EVI_OK)
            {
                fprintf_s(stdout, "%.03f %.03f %d\n", measurement.channel470.dark, measurement.channel470.value, measurement.channel470.ledPower);
            }
            else
            {
                printError(ret, NULL);
            }
        }
        break;

        case MEASUREMENT_TYPE_FIRST_AIR:
        {
            MeasurementFirstAir_t measurement;
            ret = eviFluorMeasureFirstAir(self, &measurement);
            fprintf_s(stdout, "%.03f %.03f %d %.03f %.03f %d\n", measurement.min.channel470.dark, measurement.min.channel470.value, measurement.min.channel470.ledPower, measurement.max.channel470.dark, measurement.max.channel470.value, measurement.max.channel470.ledPower);
        }
        break;

        case MEASUREMENT_TYPE_FIRST_SAMPLE:
        {
            MeasurementFirstSample_t measurement;
            ret = eviFluorMeasureFirstSample(self, &measurement);
            fprintf_s(stdout, "%.03f %.03f %d %d %d\n", measurement.measurement.channel470.dark, measurement.measurement.channel470.value, measurement.measurement.channel470.ledPower, measurement.autogain.found, measurement.autogain.ledPower);
        }
        break;
    }


exit:
    return ret;
}

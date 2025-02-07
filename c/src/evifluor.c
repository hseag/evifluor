// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "evifluor.h"
#include "evifluorindex.h"
#include <stdio.h>
#include <stdlib.h>

typedef struct
{
    SingleMeasurement_t * measurement;
} UserMeasurement;

Error_t eviFluorMeasure_(EvieResponse_t *response, void *user)
{
	UserMeasurement *u = (UserMeasurement *)user;
    if (response->argc == 7)
	{
        u->measurement->channel470.dark     = atof(response->argv[1]);
        u->measurement->channel470.value    = atof(response->argv[2]);
        u->measurement->channel470.ledPower = atoi(response->argv[3]);
        return ERROR_EVI_OK;
	}
	else
	{
        return ERROR_EVI_PROTOCOL_ERROR;
	}
}

typedef struct
{
    Autogain_t * autogain;
} UserAutogain;

Error_t eviFluorAutogain_(EvieResponse_t *response, void *user)
{
    UserAutogain *u = (UserAutogain *)user;
    if (response->argc == 3)
    {
        u->autogain->found     = atoi(response->argv[1]);
        u->autogain->ledPower  = atoi(response->argv[2]);
        return ERROR_EVI_OK;
    }
    else
    {
        return ERROR_EVI_PROTOCOL_ERROR;
    }
}

typedef struct
{
    bool * empty;
} UserEmpty;

Error_t eviFluorIsCuvetteHolderEmpty_(EvieResponse_t *response, void *user)
{
    UserEmpty *u = (UserEmpty *)user;
    if (response->argc >= 2)
    {
        (*u->empty) = atoi(response->argv[1]);
        return ERROR_EVI_OK;
    }
    else
    {
        return ERROR_EVI_PROTOCOL_ERROR;
    }
}

Error_t eviFluorMeasure(Evi_t * self, SingleMeasurement_t * measurement)
{
    UserMeasurement user = {measurement = measurement};
    return eviExecute(self, "M", eviFluorMeasure_, &user);
}

Error_t eviFluorAutogain(Evi_t *self, uint32_t level, Autogain_t * autogain)
{
    UserAutogain user = {autogain = autogain};

    char cmd[EVI_MAX_LINE_LENGTH];
    sprintf_s(cmd, EVI_MAX_LINE_LENGTH, "C %i", level);
    return eviExecute(self, cmd, eviFluorAutogain_, &user);
}

Error_t eviFluorMeasureFirstAir(Evi_t * self, MeasurementFirstAir_t * measurement)
{
    Error_t ret = ERROR_EVI_OK;
    char valueMin[10];
    char valueMax[10];

    ret = eviGet(self, INDEX_CURRENT_LED470_POWER_MIN, valueMin, sizeof(valueMin));
    if(ret != ERROR_EVI_OK) goto exit;

    ret = eviGet(self, INDEX_CURRENT_LED470_POWER_MAX, valueMax, sizeof(valueMax));
    if(ret != ERROR_EVI_OK) goto exit;

    ret = eviSet(self, INDEX_CURRENT_LED470_POWER, valueMin);
    if(ret != ERROR_EVI_OK) goto exit;

    ret = eviFluorMeasure(self, &(measurement->min));
    if(ret != ERROR_EVI_OK) goto exit;

    ret = eviSet(self, INDEX_CURRENT_LED470_POWER, valueMax);
    if(ret != ERROR_EVI_OK) goto exit;

    ret = eviFluorMeasure(self, &(measurement->max));
    if(ret != ERROR_EVI_OK) goto exit;

exit:
    return ret;
}

Error_t eviFluorMeasureFirstSample(Evi_t * self, MeasurementFirstSample_t * measurement)
{
    Error_t ret = ERROR_EVI_OK;
    ret = eviFluorAutogain(self, 2000, &(measurement->autogain));
    if(ret != ERROR_EVI_OK) goto exit;

    ret = eviFluorMeasure(self, &(measurement->measurement));
    if(ret != ERROR_EVI_OK) goto exit;

exit:
    return ret;
}

Error_t eviFluorLastMeasurements(Evi_t * self, uint32_t last, SingleMeasurement_t * measurement)
{
    UserMeasurement user = {measurement = measurement};
    char cmd[EVI_MAX_LINE_LENGTH];
    sprintf_s(cmd, EVI_MAX_LINE_LENGTH, "M %i", last);
    return eviExecute(self, cmd, eviFluorMeasure_, &user);
}

Error_t eviFluorBaseline(Evi_t * self)
{
    return eviExecute(self, "G", eviNoReturn_, 0);
}

Error_t eviFluorIsCuvetteHolderEmpty(Evi_t * self, bool * empty)
{
    UserEmpty user = {empty = empty};
    return eviExecute(self, "X", eviFluorIsCuvetteHolderEmpty_, &user);
}

SingleMeasurement_t eviFluorAdjustToLedPower(const SingleMeasurement_t * minMeasurement, const SingleMeasurement_t * maxMeasurement, uint8_t ledPower)
{
    SingleMeasurement_t ret = {0};

    ret.channel470.ledPower = ledPower;
    ret.channel470.dark     = minMeasurement->channel470.dark + (maxMeasurement->channel470.dark - minMeasurement->channel470.dark) / (maxMeasurement->channel470.ledPower - minMeasurement->channel470.ledPower) * (ledPower - minMeasurement->channel470.ledPower);
    ret.channel470.value    = minMeasurement->channel470.value + (maxMeasurement->channel470.value - minMeasurement->channel470.value) / (maxMeasurement->channel470.ledPower - minMeasurement->channel470.ledPower) * (ledPower - minMeasurement->channel470.ledPower);

    return ret;
}

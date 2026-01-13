// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "singlemeasurement.h"
#include "evibase.h"
#include "dict.h"

SingleMeasurement_t singleMeasurement_init(Channel_t channel470)
{
    SingleMeasurement_t ret = {.channel470 = channel470};

    return ret;
}

double singleMeasurement_delta(const SingleMeasurement_t * self)
{
    return channel_delta(&self->channel470);
}

void singleMeasurement_print(const SingleMeasurement_t * self, FILE * stream, bool newLine)
{
    fprintf_s(stream, "470: [");
    channel_print(&self->channel470, stream, false);
    fprintf_s(stream, "]%s", newLine ? "\n" : "");
}

cJSON* singleMeasurement_toJson(const SingleMeasurement_t * measurement)
{
    cJSON* obj = cJSON_CreateObject();
    cJSON_AddItemToObject(obj, DICT_DARK, cJSON_CreateNumber(measurement->channel470.dark));
    cJSON_AddItemToObject(obj, DICT_VALUE, cJSON_CreateNumber(measurement->channel470.value));
    cJSON_AddItemToObject(obj, DICT_LED_POWER, cJSON_CreateNumber(measurement->channel470.ledPower));
    return obj;
}

SingleMeasurement_t singleMeasurement_fromJsonValid(cJSON* obj, bool * valid)
{
    SingleMeasurement_t ret = {};
    *valid = singleMeasurement_fromJson(obj, &ret);
    return ret;
}

bool singleMeasurement_fromJson(cJSON* obj, SingleMeasurement_t * measurement)
{
    bool ret = false;

    cJSON * oDark = cJSON_GetObjectItem(obj, DICT_DARK);
    cJSON * oValue = cJSON_GetObjectItem(obj, DICT_VALUE);
    cJSON * oLedPower = cJSON_GetObjectItem(obj, DICT_LED_POWER);
    if(oDark && oValue && oLedPower)
    {
        measurement->channel470.dark = cJSON_GetNumberValue(oDark);
        measurement->channel470.value = cJSON_GetNumberValue(oValue);
        measurement->channel470.ledPower = cJSON_GetNumberValue(oLedPower);
        ret = true;
    }
    return ret;
}

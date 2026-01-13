// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "measurement.h"
#include "verification.h"
#include "evibase.h"
#include "evifluor.h"
#include "singlemeasurement.h"
#include "dict.h"

Measurement_t measurement_init(SingleMeasurement_t air, SingleMeasurement_t sample)
{
    Measurement_t ret = {.air = air, .sample = sample};

    return ret;
}

void measurement_print(const Measurement_t * self, FILE * stream, bool newLine)
{
    fprintf_s(stream, " ");
    fprintf_s(stream, "air: ");
    singleMeasurement_print(&self->air, stream, false);
    fprintf_s(stream, " ");
    fprintf_s(stream, "sample: ");
    singleMeasurement_print(&self->sample, stream, false);
    fprintf_s(stream, "%s", newLine ? "\n" : "");
}

Factors_t measurement_calculateFactors(double concentrationLow, double concentrationHigh, const Measurement_t *measurementStdLow, const Measurement_t *measurementStdHigh)
{
    Factors_t ret = {0};

    ret.stdLow.concentration = concentrationLow;
    ret.stdLow.value = measurement_value(measurementStdLow);

    ret.stdHigh.concentration = concentrationHigh;
    ret.stdHigh.value = measurement_value(measurementStdHigh);

    return ret;
}

double measurement_concentration(const Measurement_t * self, const Factors_t * factors)
{
    double m = (factors->stdHigh.concentration - factors->stdLow.concentration) / (factors->stdHigh.value - factors->stdLow.value);
    double b = factors->stdHigh.concentration - m * factors->stdHigh.value;
    return m * measurement_value(self) + b;
}

double measurement_value(const Measurement_t * self)
{
    return singleMeasurement_delta(&self->sample) - singleMeasurement_delta(&self->air);
}

Measurement_t measurement_fromJsonValid(cJSON * obj, bool * valid)
{
    Measurement_t ret = {};
    *valid = measurement_fromJson(obj, &ret);
    return ret;

}

bool measurement_fromJson(cJSON * obj, Measurement_t * measurement)
{
    bool ret = false;
    cJSON* oAir = cJSON_GetObjectItem(obj, DICT_AIR);
    cJSON* oSample = cJSON_GetObjectItem(obj, DICT_SAMPLE);
    if(oAir && oSample)
    {
        SingleMeasurement_t air = {};
        SingleMeasurement_t sample = {};
        if(singleMeasurement_fromJson(oAir, &air) && singleMeasurement_fromJson(oSample, &sample))
        {
            *measurement = measurement_init(air, sample);
            ret = true;
        }
    }

    return ret;
}

static bool getSupportPointAtIndex(cJSON* oMeasurments, uint32_t index, Measurement_t * measurement)
{
    bool ret = false;

    if (index < cJSON_GetArraySize(oMeasurments))
    {
        cJSON* oMeasurement = cJSON_GetArrayItem(oMeasurments, index);
        if (oMeasurement)
        {
            bool valid;
            *measurement = measurement_fromJsonValid(oMeasurement, &valid);
            if(valid)
            {
                ret = true;
            }
            else
            {
                cJSON* values = cJSON_GetObjectItem(oMeasurement, DICT_VALUES);
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
                        measurement->sample   = singleMeasurement_fromJsonValid(oSample, &valid1);
                        minMeasurement        = singleMeasurement_fromJsonValid(oMin, &valid2);
                        maxMeasurement        = singleMeasurement_fromJsonValid(oMax, &valid3);

                        if(valid1 && valid2 && valid3)
                        {
                            measurement->air = eviFluorAdjustToLedPower(&minMeasurement, &maxMeasurement, measurement->sample.channel470.ledPower);

                            cJSON_AddItemToObject(oMeasurement, DICT_AIR, singleMeasurement_toJson(&(measurement->air)));
                            cJSON_AddItemToObject(oMeasurement, DICT_SAMPLE, singleMeasurement_toJson(&(measurement->sample)));

                            ret = true;
                        }
                    }
                }
            }
        }
    }
    return ret;
}

bool measurement_calculatePoint(cJSON *oMeasurments, double concentration, uint32_t start, uint32_t count, Point_t * point)
{
    Measurement_t m = {};

    point->concentration = concentration;
    point->value         = 0.0;

    for(uint32_t i=start; i<(start+count);i++)
    {
        if(getSupportPointAtIndex(oMeasurments, i, &m))
        {
            point->value += measurement_value(&m);
        }
        else
        {
            return false;
        }
    }
    point->value /= count;
    return true;
}

static cJSON *calculate(cJSON *obj, Factors_t * factors, double * concentration)
{
    cJSON *ret = cJSON_CreateObject();
    bool valid;

    Measurement_t measurement = measurement_fromJsonValid(obj, &valid);

    if(valid)
    {
        *concentration = measurement_concentration(&measurement, factors);

        cJSON_AddNumberToObject(ret, DICT_CONCENTRATION, *concentration);
    }

    return ret;
}

bool measurement_calculate(cJSON * oMeasurements, double concentrationLow, double concentrationHigh, int nrOfStdLow, int nrOfStdLHigh)
{
    bool ret = false;

    if (oMeasurements)
    {
        Factors_t factors = {};

        if(measurement_calculatePoint(oMeasurements, concentrationHigh, 0, nrOfStdLHigh, &factors.stdHigh) && measurement_calculatePoint(oMeasurements, concentrationLow, nrOfStdLHigh, nrOfStdLow, &factors.stdLow))
        {
                cJSON *iterator = NULL;
                cJSON_ArrayForEach(iterator, oMeasurements)
                {
                    double concentration = 0.0;
                    cJSON_DeleteItemFromObject(iterator, DICT_CALCULATED);                    
                    cJSON_AddItemToObject(iterator, DICT_CALCULATED, calculate(iterator, &factors, &concentration));

                    cJSON * oErrors = cJSON_GetObjectItem(iterator, DICT_ERRORS);
                    Verification_t v;

                    if(oErrors == NULL)
                    {
                        v = verification_init();
                    }
                    else
                    {
                        v = verification_fromJson(oErrors);
                    }

                    if(!verification_checkResult(&v, concentration, HINTS_NONE))
                    {
                        if(oErrors == NULL)
                        {
                            cJSON_AddItemToObject(iterator, DICT_ERRORS, verification_toJson(&v));
                        }
                        else
                        {
                            cJSON_ReplaceItemInObject(iterator, DICT_ERRORS, verification_toJson(&v));
                        }
                    }
                }
                ret = true;
        }
    }
    return ret;
}

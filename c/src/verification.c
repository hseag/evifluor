// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "verification.h"
#include "evibase.h"
#include "dict.h"

#define DEFAULT_MIN_RFU                          4.5
#define DEFAULT_MAX_RFU                          35.0
#define DEFAULT_MIN_LED                          32
#define DEFAULT_MAX_LED                          222
#define DEFAULT_THRESHOLD_MULTIPLIER             2.0
#define DEFAULT_MAX_SIGNAL                       2499.0
#define DEFAULT_STD_HIGH_TARGET                  2000.0
#define DEFAULT_STD_HIGH_DELTA                   300
#define DEFAULT_THRESHOLD_NEGATIVE_CONCENTRATION -0.1

static double min_rfu                          = DEFAULT_MIN_RFU;
static double max_rfu                          = DEFAULT_MAX_RFU;
static double min_led                          = DEFAULT_MIN_LED;
static double max_led                          = DEFAULT_MAX_LED;
static double threshold_multiplier             = DEFAULT_THRESHOLD_MULTIPLIER;
static double max_signal                       = DEFAULT_MAX_SIGNAL;
static double std_high_target                  = DEFAULT_STD_HIGH_TARGET;
static double std_high_delta                   = DEFAULT_STD_HIGH_DELTA;
static double threshold_negative_concentration = DEFAULT_THRESHOLD_NEGATIVE_CONCENTRATION;

void   verification_setMinRfu(double value)
{
    min_rfu = value;
}

double verification_getMinRfu()
{
    return min_rfu;
}

void   verification_resetMinRfu()
{
    min_rfu = DEFAULT_MIN_RFU;
}

void   verification_setMaxRfu(double value)
{
    max_rfu = value;
}

double verification_getMaxRfu()
{
    return max_rfu;
}

void   verification_resetMaxRfu()
{
    max_rfu = DEFAULT_MAX_RFU;
}

void   verification_setMinLed(double value)
{
    min_led = value;
}

double verification_getMinLed()
{
    return min_led;
}

void   verification_resetMinLed()
{
    min_led = DEFAULT_MIN_LED;
}

void   verification_setMaxLed(double value)
{
    max_led = value;
}

double verification_getMaxLed()
{
    return max_led;
}

void   verification_resetMaxLed()
{
    min_led = DEFAULT_MAX_LED;
}

void   verification_setThresholdMultiplier(double value)
{
    threshold_multiplier = value;
}

double verification_getThresholdMultiplier()
{
    return threshold_multiplier;
}

void   verification_resetThresholdMultiplier()
{
    threshold_multiplier = DEFAULT_THRESHOLD_MULTIPLIER;
}

void   verification_setMaxSignal(double value)
{
    max_signal = value;
}

double verification_getMaxSignal()
{
    return max_signal;
}

void   verification_resetMaxSignal()
{
    max_signal = DEFAULT_MAX_SIGNAL;
}

void   verification_setStdHighTarget(double value)
{
    std_high_target = value;
}

double verification_getStdHighTarget()
{
    return std_high_target;
}

void   verification_resetStdHighTarget()
{
    std_high_target = DEFAULT_STD_HIGH_TARGET;
}

void   verification_setStdHighDelta(double value)
{
    std_high_delta = value;
}

double verification_getStdHighDelta()
{
    return std_high_delta;
}

void   verification_resetStdHighDelta()
{
    std_high_delta = DEFAULT_STD_HIGH_DELTA;
}

void   verification_setThresholdNegativeConcentration(double value)
{
    threshold_negative_concentration = value;
}

double verification_getThresholdNegativeConcentrationa()
{
    return threshold_negative_concentration;
}

void   verification_resetThresholdNegativeConcentration()
{
    threshold_negative_concentration = DEFAULT_THRESHOLD_NEGATIVE_CONCENTRATION;
}

static cJSON * entry_toJson(const Entry_t * self)
{
    cJSON * obj = cJSON_CreateObject();
    cJSON_AddItemToObject(obj, "problem_id", cJSON_CreateNumber(self->problemId));
    cJSON_AddItemToObject(obj, "description", cJSON_CreateString(problemId_toString(self->problemId)));
    return obj;
}

static Entry_t entry_fromJson(cJSON * obj)
{
    Entry_t ret = {};

    ret.problemId = cJSON_GetNumberValue(cJSON_GetObjectItem(obj, "problem_id"));

    return ret;
}

static double expected_value(uint8_t led_power)
{
    double slope = (max_rfu - min_rfu) / (max_led - min_led);
    return min_rfu + slope * (led_power - min_led);
}

static bool has_cuvette(const SingleMeasurement_t * sm)
{
    double expected = expected_value(sm->channel470.ledPower);
    return singleMeasurement_delta(sm) > expected * threshold_multiplier;
}

static void verification_addProblemId(Verification_t * self, ProblemId_t problemId)
{
    if(!verification_hasProblem(self, problemId))
    {
        if(self->entriesCount < MAX_ENTRIES)
        {
            self->entries[self->entriesCount].problemId = problemId;
            self->entriesCount++;
        }
    }
}

const char * problemId_toString(ProblemId_t problemId)
{
    switch (problemId)
    {
        case PROBLEM_ID_SATURATION:
            return "SATURATION";
        case PROBLEM_ID_CUVETTE_MISSING:
            return "CUVETTE_MISSING";
        case PROBLEM_ID_MIN_LED_POWER:
            return "MIN_LED_POWER";
        case PROBLEM_ID_MAX_LED_POWER:
            return "MAX_LED_POWER";
        case PROBLEM_ID_AUTO_GAIN_RESULT:
            return "AUTO_GAIN_RESULT";
        case PROBLEM_ID_WRONG_LEVEL:
            return "WRONG_LEVEL";
        case PROBLEM_ID_NEGATIVE_CONCENTRATION:
            return "NEGATIVE_CONCENTRATION";
        default:
            return "Unknown problem Id";
    }
}

Verification_t verification_init()
{
    Verification_t ret = { 0 };

    return ret;
}

bool verification_failed(const Verification_t * self)
{
    return self->entriesCount > 0 ? true : false;
}

bool verification_hasProblem(const Verification_t * self, ProblemId_t problemId)
{
    for(size_t i=0; i<self->entriesCount; i++)
    {
        if(self->entries[i].problemId == problemId)
        {
            return true;
        }
    }
    return false;
}

bool verification_checkAutoGainResult(Verification_t * self, const Autogain_t * autoGainResult, Hints_t hints)
{
    (void)hints;
    bool ret = true;
    if (!autoGainResult->found == true)
    {
        verification_addProblemId(self, PROBLEM_ID_AUTO_GAIN_RESULT);
        ret = false;
    }

    return ret;
}

DLLEXPORT bool verification_checkSingleMeasurement(Verification_t *self, const SingleMeasurement_t * singleMeasurement, Hints_t hints)
{
    bool ret = true;

    if(singleMeasurement->channel470.value >= max_signal)
    {
        verification_addProblemId(self, PROBLEM_ID_SATURATION);
        ret = false;
    }

     if((HINTS_MUST_HAVE_CUVETTE & hints) != 0)
    {
        if(!(has_cuvette(singleMeasurement) == true))
        {
            verification_addProblemId(self, PROBLEM_ID_CUVETTE_MISSING);
            ret = false;
        }
    }

    if((HINTS_STD_HIGH & hints) != 0)
    {
        if (!(singleMeasurement->channel470.value >= (std_high_target - std_high_delta) && singleMeasurement->channel470.value <= (std_high_target + std_high_delta)))
        {
            verification_addProblemId(self, PROBLEM_ID_WRONG_LEVEL);
            ret = false;
        }
    }

    return ret;
}

bool verification_checkMeasurement(Verification_t *self, const Measurement_t * measurement, Hints_t hints)
{
    bool ret1 = verification_checkSingleMeasurement(self, &measurement->air, HINTS_MUST_HAVE_CUVETTE );
    bool ret2 = verification_checkSingleMeasurement(self, &measurement->sample, (hints | HINTS_MUST_HAVE_CUVETTE));
    return ret1 && ret2;
}

bool verification_checkResult(Verification_t *self, double concentration, Hints_t hints)
{
    (void)hints;
    bool ret;
    if(concentration < threshold_negative_concentration)
    {
        verification_addProblemId(self, PROBLEM_ID_NEGATIVE_CONCENTRATION);
        ret = false;
    }
    else
    {
        ret = true;
    }
    return ret;
}

bool verification_checkFirstAirMasurementResult(Verification_t *self, const MeasurementFirstAir_t * fam, Hints_t hints)
{
    bool ret1 = verification_checkSingleMeasurement(self, &fam->min, HINTS_MUST_HAVE_CUVETTE);
    bool ret2 = verification_checkSingleMeasurement(self, &fam->max, HINTS_MUST_HAVE_CUVETTE);
    return ret1 && ret2;
}

bool verification_checkFirstSampleMeasurementResult(Verification_t *self, const MeasurementFirstSample_t * fsm, Hints_t hints)
{
    bool ret1 = verification_checkAutoGainResult(self, &fsm->autogain, hints);
    bool ret2 = verification_checkSingleMeasurement(self, &fsm->measurement,  HINTS_MUST_HAVE_CUVETTE | HINTS_STD_HIGH);
    return ret1 && ret2;
}

cJSON* verification_toJson(const Verification_t *self)
{
    cJSON* obj = cJSON_CreateArray();

    for(size_t i=0; i<self->entriesCount; i++)
    {
        cJSON_AddItemToArray(obj, entry_toJson(self->entries + i));
    }

    return obj;
}

Verification_t verification_fromJson(cJSON * obj)
{
    Verification_t ret = verification_init();

    cJSON *iterator = NULL;
    cJSON_ArrayForEach(iterator, obj)
    {
        if(ret.entriesCount < MAX_ENTRIES)
        {
            ret.entries[ret.entriesCount] = entry_fromJson(iterator);
            ret.entriesCount++;
        }
    }

    return ret;
}

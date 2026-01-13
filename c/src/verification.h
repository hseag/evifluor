// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include <stdbool.h>
#include "cJSON.h"
#include "evifluor.h"
#include "measurement.h"

#if defined(_WIN64) || defined(_WIN32)
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

#define MAX_ENTRIES 10 /**< Maximum number of verification entries tracked. */

/**
 * @brief Enumerates possible problems detected during verification.
 */
typedef enum
{
    PROBLEM_ID_SATURATION             = 1, /**< Signal exceeds allowed range. */
    PROBLEM_ID_CUVETTE_MISSING        = 2, /**< No cuvette detected during measurement. */
    PROBLEM_ID_MIN_LED_POWER          = 3, /**< LED power below acceptable minimum. */
    PROBLEM_ID_MAX_LED_POWER          = 4, /**< LED power above acceptable maximum. */
    PROBLEM_ID_AUTO_GAIN_RESULT       = 5, /**< Autogain routine did not converge. */
    PROBLEM_ID_WRONG_LEVEL            = 6, /**< Fluorescence level outside tolerance. */
    PROBLEM_ID_NEGATIVE_CONCENTRATION = 7, /**< Calculated concentration is negative. */
} ProblemId_t;

/**
 * @brief Bitmask of optional hints influencing verification thresholds.
 */
typedef enum
{
    HINTS_NONE              = 0, /**< Use default verification limits. */
    HINTS_MUST_HAVE_CUVETTE = 1, /**< Require that a cuvette is present. */
    HINTS_STD_HIGH          = 2, /**< Enforce tighter checks for high standard. */
} Hints_t;

/**
 * @brief Records a single verification issue.
 */
typedef struct
{
    ProblemId_t problemId; /**< Reported problem identifier. */
} Entry_t;

/**
 * @brief Collects verification issues produced while analysing measurements.
 */
typedef struct
{
    Entry_t entries[MAX_ENTRIES]; /**< Circular buffer of collected issues. */
    size_t entriesCount;          /**< Number of populated entries. */
} Verification_t;

/**
 * @brief Returns a human readable label for a problem identifier.
 *
 * @param problemId Problem identifier to convert.
 * @return Constant string literal describing the problem.
 */
DLLEXPORT const char * problemId_toString(ProblemId_t problemId);

/**
 * @brief Creates a verification object with default thresholds.
 *
 * @return Initialized verification state.
 */
DLLEXPORT Verification_t verification_init();
/**
 * @brief Checks whether verification succeeded without issues.
 *
 * @param self Verification instance to query.
 * @return true when no problems were registered.
 */
DLLEXPORT bool verification_success(const Verification_t * self);
/**
 * @brief Checks whether any problem has been recorded.
 *
 * @param self Verification instance to query.
 * @return true when at least one problem exists.
 */
DLLEXPORT bool verification_failed(const Verification_t * self);
/**
 * @brief Tests whether a specific problem is present.
 *
 * @param self Verification instance to query.
 * @param problemId Problem identifier to look for.
 * @return true when the given problem was registered.
 */
DLLEXPORT bool verification_hasProblem(const Verification_t * self, ProblemId_t problemId);
/**
 * @brief Validates the autogain result against hint dependent thresholds.
 *
 * @param self Verification instance collecting issues.
 * @param autoGainResult Autogain outcome to evaluate.
 * @param hints Optional hints to adapt thresholds.
 * @return true when the result is acceptable.
 */
DLLEXPORT bool verification_checkAutoGainResult(Verification_t *self, const Autogain_t * autoGainResult, Hints_t hints);
/**
 * @brief Validates a single measurement for saturation and consistency.
 *
 * @param self Verification instance collecting issues.
 * @param singleMeasurement Measurement to check.
 * @param hints Optional hints to adapt thresholds.
 * @return true when the measurement passes all checks.
 */
DLLEXPORT bool verification_checkSingleMeasurement(Verification_t *self, const SingleMeasurement_t * singleMeasurement, Hints_t hints);
/**
 * @brief Validates an air/sample pair measurement.
 *
 * @param self Verification instance collecting issues.
 * @param measurement Measurement to check.
 * @param hints Optional hints to adapt thresholds.
 * @return true when the measurement passes all checks.
 */
DLLEXPORT bool verification_checkMeasurement(Verification_t *self, const Measurement_t * measurement, Hints_t hints);
/**
 * @brief Validates a computed concentration.
 *
 * @param self Verification instance collecting issues.
 * @param concentration Calculated concentration value.
 * @param hints Optional hints to adapt thresholds.
 * @return true when the result is within acceptable limits.
 */
DLLEXPORT bool verification_checkResult(Verification_t *self, double concentration, Hints_t hints);
/**
 * @brief Validates the first-air measurement range collected during setup.
 *
 * @param self Verification instance collecting issues.
 * @param fam Pointer to the range data.
 * @param hints Optional hints to adapt thresholds.
 * @return true when the result is acceptable.
 */
DLLEXPORT bool verification_checkFirstAirMasurementResult(Verification_t *self, const MeasurementFirstAir_t * fam, Hints_t hints);
/**
 * @brief Validates the first-sample measurement including autogain data.
 *
 * @param self Verification instance collecting issues.
 * @param fsm First sample measurement.
 * @param hints Optional hints to adapt thresholds.
 * @return true when the result is acceptable.
 */
DLLEXPORT bool verification_checkFirstSampleMeasurementResult(Verification_t *self, const MeasurementFirstSample_t * fsm, Hints_t hints);

/**
 * @name Threshold configuration helpers
 * @brief Configure runtime limits used by the verification layer.
 */
/** @{ */
DLLEXPORT void   verification_setMinRfu(double value);
DLLEXPORT double verification_getMinRfu();
DLLEXPORT void   verification_resetMinRfu();
DLLEXPORT void   verification_setMaxRfu(double value);
DLLEXPORT double verification_getMaxRfu();
DLLEXPORT void   verification_resetMaxRfu();
DLLEXPORT void   verification_setMinLed(double value);
DLLEXPORT double verification_getMinLed();
DLLEXPORT void   verification_resetMinLed();
DLLEXPORT void   verification_setMaxLed(double value);
DLLEXPORT double verification_getMaxLed();
DLLEXPORT void   verification_resetMaxLed();
DLLEXPORT void   verification_setThresholdMultiplier(double value);
DLLEXPORT double verification_getThresholdMultiplier();
DLLEXPORT void   verification_resetThresholdMultiplier();
DLLEXPORT void   verification_setMaxSignal(double value);
DLLEXPORT double verification_getMaxSignal();
DLLEXPORT void   verification_resetMaxSignal();
DLLEXPORT void   verification_setStdHighTarget(double value);
DLLEXPORT double verification_getStdHighTarget();
DLLEXPORT void   verification_resetStdHighTarget();
DLLEXPORT void   verification_setStdHighDelta(double value);
DLLEXPORT double verification_getStdHighDelta();
DLLEXPORT void   verification_resetStdHighDelta();
DLLEXPORT void   verification_setThresholdNegativeConcentration(double value);
DLLEXPORT double verification_getThresholdNegativeConcentrationa();
DLLEXPORT void   verification_resetThresholdNegativeConcentration();
/** @} */

/**
 * @brief Serializes the verification object to JSON.
 *
 * @param self Verification instance to serialize.
 * @return Newly allocated cJSON object owned by the caller.
 */
DLLEXPORT  cJSON * verification_toJson(const Verification_t *self);

/**
 * @brief Populates a verification object from JSON.
 *
 * @param obj JSON representation of the verification state.
 * @return Parsed verification data.
 */
DLLEXPORT  Verification_t verification_fromJson(cJSON * obj);

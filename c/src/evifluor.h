// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evibase.h"
#include "singlemeasurement.h"
#include <stdint.h>

/**
 * @struct Autogain_t
 * @brief Represents the autogain detection result.
 *
 * This structure stores information about whether an optimal LED power
 * setting was found and the corresponding LED power level.
 */
typedef struct
{
    bool found; /**< Indicates whether a suitable LED power level was found. */
    uint8_t ledPower; /**< The determined LED power level. */
} Autogain_t;

/**
 * @struct MeasurementFirstAir_t
 * @brief Represents the first air measurement range.
 *
 * This structure holds the minimum and maximum single measurements for the
 * first air measurement process.
 */
typedef struct
{
    SingleMeasurement_t min; /**< Minimum detected measurement values. */
    SingleMeasurement_t max; /**< Maximum detected measurement values. */
} MeasurementFirstAir_t;

/**
 * @struct MeasurementFirstSample_t
 * @brief Represents the first sample measurement, including autogain data.
 *
 * This structure stores both the autogain results and the corresponding
 * first sample measurement values.
 */
typedef struct
{
    Autogain_t autogain; /**< Autogain result for the measurement. */
    SingleMeasurement_t measurement; /**< The recorded sample measurement. */
} MeasurementFirstSample_t;

/**
 * @brief Performs an autogain adjustment for fluorescence measurement.
 *
 * @param self Pointer to the Evi_t structure.
 * @param level The target level (0-2500) for autogain adjustment.
 * @param autogain Pointer to an Autogain_t structure to store the result.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviFluorAutogain(Evi_t *self, uint32_t level, Autogain_t * autogain);

/**
 * @brief Executes a baseline command. Actually no adjustment or measurement is performed.
 * Only the internal measurement memory is deleted.
 *
 * @param self Pointer to the Evi_t structure.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviFluorBaseline(Evi_t * self);

/**
 * @brief Measures fluorescence and stores the result.
 *
 * @param self Pointer to the Evi_t structure.
 * @param measurement Pointer to a SingleMeasurement_t structure to store the result.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviFluorMeasure(Evi_t *self, SingleMeasurement_t * measurement);

/**
 * @brief Performs the first air measurement and stores the result.
 *
 * @param self Pointer to the Evi_t structure.
 * @param measurement Pointer to a MeasurementFirstAir_t structure to store the min and max values.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviFluorMeasureFirstAir(Evi_t *self, MeasurementFirstAir_t * measurement);

/**
 * @brief Performs the first sample measurement with autogain and stores the result.
 *
 * @param self Pointer to the Evi_t structure.
 * @param measurement Pointer to a MeasurementFirstSample_t structure to store the autogain and measurement data.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviFluorMeasureFirstSample(Evi_t *self, MeasurementFirstSample_t * measurement);

/**
 * @brief Retrieves the last fluorescence measurement results.
 *
 * @param self Pointer to the Evi_t structure.
 * @param last The number of previous measurements to retrieve.
 * @param measurement Pointer to a SingleMeasurement_t structure to store the measurement data.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviFluorLastMeasurements(Evi_t * self, uint32_t last, SingleMeasurement_t * measurement);

/**
 * @brief Performs a self-test on the fluorescence measurement system.
 *
 * @param self Pointer to the Evi_t structure.
 * @param result Pointer to store the self-test result.
 * @return An error code indicating the result of the self-test.
 */
DLLEXPORT Error_t eviFluorSelftest(Evi_t *self, uint32_t *result);

/**
 * @brief Checks whether the cuvette holder is empty.
 *
 * @param self Pointer to the Evi_t structure.
 * @param empty Pointer to a boolean value that will be set to true if empty, false otherwise.
 * @return An error code indicating the result of the check.
 */
DLLEXPORT Error_t eviFluorIsCuvetteHolderEmpty(Evi_t * self, bool * empty);

/**
 * @brief Adjusts a fluorescence measurement based on LED power settings.
 *
 * @param minMeasurement Pointer to the minimum measurement values.
 * @param maxMeasurement Pointer to the maximum measurement values.
 * @param ledPower The LED power level used for adjustment.
 * @return A SingleMeasurement_t structure containing the adjusted measurement.
 */
DLLEXPORT SingleMeasurement_t eviFluorAdjustToLedPower(const SingleMeasurement_t *minMeasurement, const SingleMeasurement_t *maxMeasurement, uint8_t ledPower);

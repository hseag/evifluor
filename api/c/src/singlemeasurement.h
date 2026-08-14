// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "channel.h"
#include <stdbool.h>
#include "cJSON.h"

#if defined(_WIN64) || defined(_WIN32)
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

/**
 * @struct SingleMeasurement_t
 * @brief Represents a single fluorescence measurement.
 *
 * Each measurement currently captures the 470 nm channel which includes raw
 * dark/value readings and LED power metadata.
 */
typedef struct
{
    Channel_t channel470; /**< Fluorescence channel at 470 nm. */
} SingleMeasurement_t;

/**
 * @brief Initializes a SingleMeasurement_t structure with specified channel values.
 *
 * @param channel470 Measurement channel at 470 nm.
 * @return An initialized SingleMeasurement_t structure.
 */
DLLEXPORT SingleMeasurement_t singleMeasurement_init(Channel_t channel470);

/**
 * @brief Returns the delta value sample - dark..
 *
 * @param self Pointer to the SingleMeasurement_t structure.
 * @return Difference between sample and dark.
 */
DLLEXPORT double singleMeasurement_delta(const SingleMeasurement_t * self);

/**
 * @brief Prints the contents of a SingleMeasurement_t structure to the specified stream.
 *
 * @param self Pointer to the SingleMeasurement_t structure.
 * @param stream Output file stream where the data will be printed.
 * @param newLine Whether to add a newline at the end of the output.
 */
DLLEXPORT void singleMeasurement_print(const SingleMeasurement_t * self, FILE * stream, bool newLine);

/**
 * @brief Serializes a measurement into a newly allocated JSON object.
 *
 * @param measurement Pointer to the measurement to convert.
 * @return A cJSON object owned by the caller, or NULL on allocation failure.
 */
DLLEXPORT cJSON* singleMeasurement_toJson(const SingleMeasurement_t * measurement);

/**
 * @brief Populates a measurement from a JSON description.
 *
 * The JSON layout must match the structure produced by
 * singleMeasurement_toJson().
 *
 * @param obj JSON object containing the measurement.
 * @param measurement Output parameter for the parsed data.
 * @return true when parsing succeeds, otherwise false.
 */
DLLEXPORT bool singleMeasurement_fromJson(cJSON* obj, SingleMeasurement_t * measurement);

/**
 * @brief Parses a measurement, reporting validity without mutating on failure.
 *
 * @param obj JSON source object.
 * @param valid Optional flag set to false when required members are missing.
 * @return A measurement value; contents are undefined when @p valid becomes false.
 */
DLLEXPORT SingleMeasurement_t singleMeasurement_fromJsonValid(cJSON* obj, bool * valid);

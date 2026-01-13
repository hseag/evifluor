// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "singlemeasurement.h"
#include "cJSON.h"
#include <stdbool.h>

#if defined(_WIN64) || defined(_WIN32)
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

/**
 * @brief Represents a data point with a concentration and corresponding value.
 */
typedef struct
{
    double concentration; /**< concentration value. */
    double value; /**< measured value. */
} Point_t;

/**
 * @brief Holds low and high calibration points used to compute concentrations.
 */
typedef struct
{
    Point_t stdLow;  /**< Measurement collected at the low concentration standard. */
    Point_t stdHigh; /**< Measurement collected at the high concentration standard. */
} Factors_t;

/**
 * @struct Measurement_t
 * @brief Represents a measurement with air and sample values.
 *
 * This structure contains two single measurements (air and sample).
 */
typedef struct
{
    SingleMeasurement_t air;      /**< Air measurement. */
    SingleMeasurement_t sample;   /**< Sample measurement. */
} Measurement_t;

/**
 * @brief Initializes a Measurement_t structure with given values.
 *
 * @param air The air measurement.
 * @param sample The sample measurement.
 * @return An initialized Measurement_t structure.
 */
DLLEXPORT Measurement_t measurement_init(SingleMeasurement_t air, SingleMeasurement_t sample);

/**
 * @brief Prints the contents of a Measurement_t structure to the specified stream.
 *
 * @param self Pointer to the Measurement_t structure.
 * @param stream Output file stream where the data will be printed.
 * @param newLine Whether to add a newline at the end of the output.
 */
DLLEXPORT void measurement_print(const Measurement_t * self, FILE * stream, bool newLine);

/**
 * @brief Returns the difference between air- and sample measurement.
 *
 * @param self Pointer to the Measurement_t structure.
 * @return Difference between air- and sample measurement.
 */
DLLEXPORT double measurement_value(const Measurement_t * self);

/**
 * @brief Returns the difference between air- and sample measurement.
 *
 * @param concentrationLow The known low concentration standard.
 * @param concentrationHigh The known high concentration standard.
 * @param measurementStdLow The measurement corresponding to the low concentration.
 * @param measurementStdHigh The measurement corresponding to the high concentration.
 * @return A Factors_t object containing calculated correction factors.
 */
DLLEXPORT Factors_t measurement_calculateFactors(double concentrationLow, double concentrationHigh, const Measurement_t *measurementStdLow, const Measurement_t *measurementStdHigh);

/**
 * @brief Calculates the concentration.
 *
 * @param self Pointer to the Measurement_t structure.
 * @param factors Factor to calculate the concentration.
 * @return Concentration.
 */
DLLEXPORT double measurement_concentration(const Measurement_t * self, const Factors_t * factors);

/**
 * @brief Parses a JSON object to construct a measurement, returning validity.
 *
 * When @p valid is provided it is set to false if mandatory members are
 * missing or invalid. The returned value is unspecified if parsing fails.
 *
 * @param obj JSON object to parse.
 * @param valid Optional flag that receives the parsing result.
 * @return Measurement derived from the JSON payload.
 */
DLLEXPORT Measurement_t measurement_fromJsonValid(cJSON * obj, bool * valid);

/**
 * @brief Attempts to populate a measurement structure from JSON.
 *
 * @param obj JSON object to parse.
 * @param measurement Output parameter that receives the parsed content.
 * @return true when parsing succeeds, otherwise false.
 */
DLLEXPORT bool measurement_fromJson(cJSON * obj, Measurement_t * measurement);

/**
 * @brief Calculates concentrations for a collection of measurements.
 *
 * The function reads the JSON array in @p oMeasurements, applies the provided
 * calibration points and writes the concentration back into the JSON objects.
 *
 * @param oMeasurements JSON array with measurements to process.
 * @param concentrationLow Known concentration for the low standard.
 * @param concentrationHigh Known concentration for the high standard.
 * @param nrOfStdLow Number of low standard measurements to average.
 * @param nrOfStdLHigh Number of high standard measurements to average.
 * @return true on success when all data could be processed.
 */
DLLEXPORT bool measurement_calculate(cJSON * oMeasurements, double concentrationLow, double concentrationHigh, int nrOfStdLow, int nrOfStdLHigh);

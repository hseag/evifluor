// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "channel.h"
#include <stdbool.h>

#if defined(_WIN64) || defined(_WIN32)
#include <windows.h>
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

/**
 * @struct SingleMeasurement_t
 * @brief Represents a single measurement with channels specific wavelengths.
 *
 * This structure stores measurement data for four different wavelengths,
 * each represented by a Channel_t structure.
 */
typedef struct
{
    Channel_t channel470; /**< Measurement channel at 470 nm. */
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

// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include <stdio.h>
#include <stdbool.h>
#include <stdint.h>

#if defined(_WIN64) || defined(_WIN32)
#include <windows.h>
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

/**
 * @struct Channel_t
 * @brief Represents a measurement channel with dark and value.
 *
 * This structure holds the dark and value of a measurement channel,
 * both measured in millivolts (mV).
 */
typedef struct
{
    double dark; /**< Dark value in millivolts (mV). */
    double value; /**< Value in millivolts (mV). */
    uint32_t ledPower; /**< Led power, no unit (0..255). */

} Channel_t;

/**
 * @brief Initializes a Channel_t structure with given values.
 *
 * @param dark Dark value in millivolts (mV).
 * @param value Value in millivolts (mV).
 * @param ledPower Led power, no unit (0..255).
 * @return An initialized Channel_t structure.
 */
DLLEXPORT Channel_t channel_init(double dark, double value, uint32_t ledPower);

/**
 * @briefCalculates the difference between value and dark.
 *
 * @param self Pointer to the Channel_t structure.
 * @return difference in mV.
 */
DLLEXPORT double channel_delta(const Channel_t * self);

/**
 * @brief Prints the contents of a Channel_t structure to the specified stream.
 *
 * @param self Pointer to the Channel_t structure.
 * @param stream Output file stream where the data will be printed.
 * @param newLine Whether to add a newline at the end of the output.
 */
DLLEXPORT void channel_print(const Channel_t * self, FILE * stream, bool newLine);

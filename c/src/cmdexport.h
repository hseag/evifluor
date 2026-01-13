// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evibase.h"

/**
 * @brief Describes the available export formats.
 */
typedef enum
{
    MODE_RAW,         /**< Export raw readings as captured. */
    MODE_MEASUREMENT  /**< Export calculated measurement values. */
} ExportMode_t;

/**
 * @brief Groups command line options used during export.
 */
typedef struct
{
    char delimiter;        /**< CSV delimiter, defaults to ';'. */
    char * filenameJson;   /**< Optional JSON output path, owned by the caller. */
    char * filenameCsv;    /**< Optional CSV output path, owned by the caller. */
    ExportMode_t mode;     /**< Export mode describing the desired dataset. */
} ExportOptions_t;

/**
 * @brief Implements the `export` CLI command.
 *
 * @param self Runtime context controlling the device interaction.
 * @param argcCmd Number of command specific arguments.
 * @param argvCmd Vector of command specific arguments.
 * @return Error code describing command success or failure.
 */
Error_t cmdExport(Evi_t * self, int argcCmd, char **argvCmd);

/**
 * @brief Writes measurement data according to the provided options.
 *
 * @param options Export configuration (filenames, mode, delimiter).
 * @return Error code reported when writing files or gathering data.
 */
Error_t exportData(ExportOptions_t * options);

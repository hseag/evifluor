// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evifluor.h"
#include "cJSON.h"

/**
 * @brief Loads measurement data from disk, optionally appending to the active set.
 *
 * @param self Runtime context that receives loaded measurements.
 * @param filename Path to the JSON file.
 * @param append When true the data is appended; otherwise existing data is replaced.
 * @return Newly allocated cJSON tree or NULL on failure.
 */
cJSON* dataLoadJson(Evi_t* self, const char *filename, bool append);

/**
 * @brief Handles the `save` CLI command which persists measurements.
 *
 * @param self Runtime context with measurement data to store.
 * @param argcCmd Number of command specific arguments.
 * @param argvCmd Vector of command specific arguments.
 * @return Error code describing success or failure.
 */
Error_t cmdSave(Evi_t * self, int argcCmd, char **argvCmd);

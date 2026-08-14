// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evifluor.h"

/**
 * @brief Handles the `measure` CLI command and stores the result.
 *
 * @param self Runtime context with active device connection.
 * @param argcCmd Number of command specific arguments.
 * @param argvCmd Vector of command specific arguments.
 * @return Error code describing the result.
 */
Error_t cmdMeasure(Evi_t * self, int argcCmd, char **argvCmd);

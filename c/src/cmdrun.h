// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evifluor.h"

/**
 * @brief Executes the `run` CLI command, performing a full measurement cycle.
 *
 * @param self Runtime context with device state.
 * @param argcCmd Number of command specific arguments.
 * @param argvCmd Vector of command specific arguments.
 * @return Error code describing the result of the command.
 */
Error_t cmdRun(Evi_t * self, int argcCmd, char **argvCmd);

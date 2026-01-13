// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evifluor.h"

/**
 * @brief Handles the `data` CLI command.
 *
 * The command prints or manipulates stored measurement data depending on the
 * supplied arguments.
 *
 * @param self Runtime context controlling the device interaction.
 * @param argcCmd Number of command specific arguments.
 * @param argvCmd Vector of command specific arguments.
 * @return Error code describing the outcome.
 */
Error_t cmdData(Evi_t * self, int argcCmd, char **argvCmd);
	

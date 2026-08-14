// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evifluor.h"

/**
 * @brief Executes the baseline CLI command.
 *
 * The command resets device memory without acquiring new data.
 *
 * @param self Runtime context passed to the command handler.
 * @return Result code reported by the operation.
 */
Error_t cmdBaseline(Evi_t * self);

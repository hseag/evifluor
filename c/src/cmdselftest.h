// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evibase.h"

/**
 * @brief Handles the `selftest` CLI command.
 *
 * @param self Runtime context that receives self-test results.
 * @return Error code describing the operation outcome.
 */
Error_t cmdSelftest(Evi_t * self);

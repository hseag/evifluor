// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include "evibase.h"

/**
 * @brief Handles the `empty` CLI command that validates an empty cuvette holder.
 *
 * @param self Runtime context controlling device communication.
 * @return Error code reported by the device layer.
 */
Error_t cmdEmpty(Evi_t * self);

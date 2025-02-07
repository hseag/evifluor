// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "channel.h"
#include "evibase.h"

Channel_t channel_init(double dark, double value, uint32_t ledPower)
{
    Channel_t ret = {.dark = dark, .value = value, .ledPower = ledPower};
    return ret;
}

double channel_delta(const Channel_t * self)
{
    return self->value - self->dark;
}

void channel_print(const Channel_t * self, FILE * stream, bool newLine)
{
    fprintf_s(stream, "dark=%f, value=%f, ledPower=%d%s", self->dark, self->value, self->ledPower, newLine ? "\n" : "");
}

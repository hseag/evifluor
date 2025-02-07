// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "singlemeasurement.h"
#include "evibase.h"

SingleMeasurement_t singleMeasurement_init(Channel_t channel470)
{
    SingleMeasurement_t ret = {.channel470 = channel470};

    return ret;
}

double singleMeasurement_delta(const SingleMeasurement_t * self)
{
    return channel_delta(&self->channel470);
}

void singleMeasurement_print(const SingleMeasurement_t * self, FILE * stream, bool newLine)
{
    fprintf_s(stream, "470: [");
    channel_print(&self->channel470, stream, false);
    fprintf_s(stream, "]%s", newLine ? "\n" : "");
}

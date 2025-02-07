// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "measurement.h"

Measurement_t measurement_init(SingleMeasurement_t air, SingleMeasurement_t sample)
{
    Measurement_t ret = {.air = air, .sample = sample};

    return ret;
}

void measurement_print(const Measurement_t * self, FILE * stream, bool newLine)
{
    fprintf_s(stream, " ");
    fprintf_s(stream, "air: ");
    singleMeasurement_print(&self->air, stream, false);
    fprintf_s(stream, " ");
    fprintf_s(stream, "sample: ");
    singleMeasurement_print(&self->sample, stream, false);
    fprintf_s(stream, "%s", newLine ? "\n" : "");
}

Factors_t measurement_calculateFactors(double concentrationLow, double concentrationHigh, const Measurement_t *measurementStdLow, const Measurement_t *measurementStdHigh)
{
    Factors_t ret = {0};

    ret.stdLow.concentration = concentrationLow;
    ret.stdLow.value = measurement_value(measurementStdLow);

    ret.stdHigh.concentration = concentrationHigh;
    ret.stdHigh.value = measurement_value(measurementStdHigh);

    return ret;
}

double measurement_concentration(const Measurement_t * self, const Factors_t * factors)
{
    double m = (factors->stdHigh.concentration - factors->stdLow.concentration) / (factors->stdHigh.value - factors->stdLow.value);
    double b = factors->stdHigh.concentration - m * factors->stdHigh.value;
    return m * measurement_value(self) + b;
}

double measurement_value(const Measurement_t * self)
{
    return singleMeasurement_delta(&self->sample) - singleMeasurement_delta(&self->air);
}

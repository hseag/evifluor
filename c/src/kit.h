// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

#pragma once

#include "cJSON.h"
#include <stdbool.h>

#if defined(_WIN64) || defined(_WIN32)
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

typedef enum
{
    KIT_FIT_LINEAR = 1,
    KIT_FIT_POWER = 2,
    KIT_FIT_QUADRATIC = 3,
} KitFitAlgorithm_t;

typedef struct
{
    KitFitAlgorithm_t fitAlgorithm;
    double k1;
    double k2;
    double k3;
    double settlingTime;
    bool hasStdHighTargetSignalFactor;
    double stdHighTargetSignalFactor;
    const char * description;
} Kit_t;

DLLEXPORT Kit_t kit_default(void);
DLLEXPORT Kit_t kit_qubit_hs(void);
DLLEXPORT Kit_t kit_qubit_br(void);
DLLEXPORT bool kit_factory(const char *name, Kit_t *out);
DLLEXPORT double kit_apply(const Kit_t *kit, double interpolated);
DLLEXPORT cJSON * kit_toJson(const Kit_t *kit);
DLLEXPORT bool kit_fromJson(cJSON *obj, Kit_t *kit);

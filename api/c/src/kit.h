// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

#pragma once

#include "cJSON.h"
#include <stdbool.h>
#include <stddef.h>

#if defined(_WIN64) || defined(_WIN32)
#define DLLEXPORT __declspec(dllexport)
#else
#define DLLEXPORT
#endif

typedef enum
{
    KIT_FIT_LINEAR = 1,
    KIT_FIT_LOOKUP_TABLE = 2,
} KitFitAlgorithm_t;

#define KIT_LOOKUP_TABLE_MAX_ENTRIES 64

typedef struct
{
    double concentration;
    double signal;
} KitLookupTableEntry_t;

typedef struct
{
    KitFitAlgorithm_t fitAlgorithm;
    double k1;
    double k2;
    double k3;
    bool hasLookupTable;
    size_t lookupTableCount;
    KitLookupTableEntry_t lookupTable[KIT_LOOKUP_TABLE_MAX_ENTRIES];
    double settlingTime;
    bool hasStdHighTargetSignalFactor;
    double stdHighTargetSignalFactor;
    const char * description;
} Kit_t;

DLLEXPORT Kit_t kit_default(void);
DLLEXPORT Kit_t kit_qubit_hs(void);
DLLEXPORT Kit_t kit_qubit_br(void);
DLLEXPORT bool kit_factory(const char *name, Kit_t *out);
DLLEXPORT bool kit_lookupTableLoad(const char *path, Kit_t *kit);
DLLEXPORT double kit_apply(const Kit_t *kit, double interpolated, double rfu, double stdLowConcentration, double stdLowValue, double stdHighConcentration, double stdHighValue);
DLLEXPORT cJSON * kit_toJson(const Kit_t *kit);
DLLEXPORT bool kit_fromJson(cJSON *obj, Kit_t *kit);

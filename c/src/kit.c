// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

#include "kit.h"
#include <ctype.h>
#include <math.h>
#include <string.h>

#define KIT_FIT_ALGORITHM_KEY "fitAlgorithm"
#define KIT_K1_KEY "k1"
#define KIT_K2_KEY "k2"
#define KIT_K3_KEY "k3"
#define KIT_SETTLING_TIME_KEY "settlingTime"
#define KIT_STD_HIGH_TARGET_SIGNAL_FACTOR_KEY "stdHighTargetSignalFactor"
#define KIT_DESCRIPTION_KEY "description"

static const char * DEFAULT_DESCRIPTION = "Default kit with linear fit";
static const char * QUBIT_HS_DESCRIPTION = "QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit";
static const char * QUBIT_BR_DESCRIPTION = "QubitTM 1X dsDNA Broad Range (BR) Assay Kit";

static int ascii_stricmp(const char *lhs, const char *rhs)
{
    while (*lhs != '\0' && *rhs != '\0')
    {
        int lhsLower = tolower((unsigned char)*lhs);
        int rhsLower = tolower((unsigned char)*rhs);
        if (lhsLower != rhsLower)
        {
            return lhsLower - rhsLower;
        }
        lhs++;
        rhs++;
    }

    return tolower((unsigned char)*lhs) - tolower((unsigned char)*rhs);
}

Kit_t kit_default(void)
{
    Kit_t kit = {0};
    kit.fitAlgorithm = KIT_FIT_LINEAR;
    kit.k1 = 1.0;
    kit.k2 = 0.0;
    kit.k3 = 0.0;
    kit.settlingTime = 0.0;
    kit.hasStdHighTargetSignalFactor = false;
    kit.stdHighTargetSignalFactor = 0.0;
    kit.description = DEFAULT_DESCRIPTION;
    return kit;
}

Kit_t kit_qubit_hs(void)
{
    Kit_t kit = kit_default();
    kit.description = QUBIT_HS_DESCRIPTION;
    return kit;
}

Kit_t kit_qubit_br(void)
{
    Kit_t kit = kit_default();
    kit.fitAlgorithm = KIT_FIT_POWER;
    kit.k1 = 1.011658;
    kit.k2 = 1.014932;
    kit.hasStdHighTargetSignalFactor = true;
    kit.stdHighTargetSignalFactor = 0.4;
    kit.description = QUBIT_BR_DESCRIPTION;
    return kit;
}

bool kit_factory(const char *name, Kit_t *out)
{
    if (name == NULL || out == NULL)
    {
        return false;
    }

    if (ascii_stricmp(name, "default") == 0)
    {
        *out = kit_default();
        return true;
    }
    if (ascii_stricmp(name, "qubittm_1x_dsdna_high_sensitivity_hs") == 0 || ascii_stricmp(name, "qubit_hs") == 0)
    {
        *out = kit_qubit_hs();
        return true;
    }
    if (ascii_stricmp(name, "qubittm_1x_dsdna_broad_range_br") == 0 || ascii_stricmp(name, "qubit_br") == 0)
    {
        *out = kit_qubit_br();
        return true;
    }

    return false;
}

double kit_apply(const Kit_t *kit, double interpolated)
{
    Kit_t resolved = kit != NULL ? *kit : kit_default();

    switch (resolved.fitAlgorithm)
    {
        case KIT_FIT_LINEAR:
            return resolved.k1 * interpolated + resolved.k2;

        case KIT_FIT_POWER:
            if (interpolated < 0.0)
            {
                return 0.0;
            }
            return resolved.k1 * pow(interpolated, resolved.k2);

        case KIT_FIT_QUADRATIC:
            if (interpolated < 0.0)
            {
                return 0.0;
            }
            return resolved.k1 * interpolated * interpolated + resolved.k2 * interpolated + resolved.k3;

        default:
            return interpolated;
    }
}

cJSON * kit_toJson(const Kit_t *kit)
{
    Kit_t resolved = kit != NULL ? *kit : kit_default();
    cJSON *obj = cJSON_CreateObject();

    cJSON_AddNumberToObject(obj, KIT_FIT_ALGORITHM_KEY, resolved.fitAlgorithm);
    cJSON_AddNumberToObject(obj, KIT_K1_KEY, resolved.k1);
    cJSON_AddNumberToObject(obj, KIT_K2_KEY, resolved.k2);
    cJSON_AddNumberToObject(obj, KIT_K3_KEY, resolved.k3);
    cJSON_AddNumberToObject(obj, KIT_SETTLING_TIME_KEY, resolved.settlingTime);
    if (resolved.hasStdHighTargetSignalFactor)
    {
        cJSON_AddNumberToObject(obj, KIT_STD_HIGH_TARGET_SIGNAL_FACTOR_KEY, resolved.stdHighTargetSignalFactor);
    }
    else
    {
        cJSON_AddNullToObject(obj, KIT_STD_HIGH_TARGET_SIGNAL_FACTOR_KEY);
    }
    cJSON_AddStringToObject(obj, KIT_DESCRIPTION_KEY, resolved.description != NULL ? resolved.description : DEFAULT_DESCRIPTION);

    return obj;
}

bool kit_fromJson(cJSON *obj, Kit_t *kit)
{
    if (kit == NULL)
    {
        return false;
    }

    if (obj == NULL)
    {
        *kit = kit_default();
        return true;
    }

    cJSON *fitAlgorithm = cJSON_GetObjectItem(obj, KIT_FIT_ALGORITHM_KEY);
    cJSON *k1 = cJSON_GetObjectItem(obj, KIT_K1_KEY);
    cJSON *k2 = cJSON_GetObjectItem(obj, KIT_K2_KEY);
    if (fitAlgorithm == NULL || k1 == NULL || k2 == NULL)
    {
        return false;
    }

    *kit = kit_default();
    kit->fitAlgorithm = (KitFitAlgorithm_t)cJSON_GetNumberValue(fitAlgorithm);
    kit->k1 = cJSON_GetNumberValue(k1);
    kit->k2 = cJSON_GetNumberValue(k2);

    {
        cJSON *k3 = cJSON_GetObjectItem(obj, KIT_K3_KEY);
        if (k3 != NULL)
        {
            kit->k3 = cJSON_GetNumberValue(k3);
        }
    }

    {
        cJSON *settlingTime = cJSON_GetObjectItem(obj, KIT_SETTLING_TIME_KEY);
        if (settlingTime != NULL)
        {
            kit->settlingTime = cJSON_GetNumberValue(settlingTime);
        }
    }

    {
        cJSON *stdHighTargetSignalFactor = cJSON_GetObjectItem(obj, KIT_STD_HIGH_TARGET_SIGNAL_FACTOR_KEY);
        if (stdHighTargetSignalFactor != NULL && !cJSON_IsNull(stdHighTargetSignalFactor))
        {
            kit->hasStdHighTargetSignalFactor = true;
            kit->stdHighTargetSignalFactor = cJSON_GetNumberValue(stdHighTargetSignalFactor);
        }
    }

    {
        cJSON *description = cJSON_GetObjectItem(obj, KIT_DESCRIPTION_KEY);
        if (description != NULL && cJSON_GetStringValue(description) != NULL)
        {
            kit->description = cJSON_GetStringValue(description);
        }
    }

    return true;
}

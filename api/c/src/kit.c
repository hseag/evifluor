// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2026 HSE AG, <opensource@hseag.com>

#include "kit.h"
#include <ctype.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define KIT_FIT_ALGORITHM_KEY "fitAlgorithm"
#define KIT_K1_KEY "k1"
#define KIT_K2_KEY "k2"
#define KIT_K3_KEY "k3"
#define KIT_LOOKUP_TABLE_KEY "lookupTable"
#define KIT_SETTLING_TIME_KEY "settlingTime"
#define KIT_STD_HIGH_TARGET_SIGNAL_FACTOR_KEY "stdHighTargetSignalFactor"
#define KIT_DESCRIPTION_KEY "description"

static const char * DEFAULT_DESCRIPTION = "Default kit with linear fit";
static const char * QUBIT_HS_DESCRIPTION = "QubitTM 1X dsDNA High Sensitivity (HS) Assay Kit";
static const char * QUBIT_BR_DESCRIPTION = "QubitTM 1X dsDNA Broad Range (BR) Assay Kit";

static const KitLookupTableEntry_t QUBIT_BR_LOOKUP_TABLE[] =
{
    {0.0, 8.21960772015573e-19},
    {0.655, 0.005511528146509457},
    {1.15, 0.012096556749881238},
    {10.3, 0.11696146388117148},
    {42.9, 0.4437930749162957},
    {80.5, 0.8584075257182888},
    {100.0, 1.0},
    {101.0, 1.029219428556792},
    {166.0, 1.4952711926922733},
    {242.0, 1.9368286353950304},
};

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

static void kit_setLookupTableEntries(Kit_t *kit, const KitLookupTableEntry_t *entries, size_t count)
{
    size_t i;

    if (kit == NULL)
    {
        return;
    }

    kit->hasLookupTable = count > 0U;
    kit->lookupTableCount = count;
    for (i = 0; i < count && i < KIT_LOOKUP_TABLE_MAX_ENTRIES; i++)
    {
        kit->lookupTable[i] = entries[i];
    }
}

static int lookupTableEntryCompare(const void *lhs, const void *rhs)
{
    const KitLookupTableEntry_t *left = (const KitLookupTableEntry_t *)lhs;
    const KitLookupTableEntry_t *right = (const KitLookupTableEntry_t *)rhs;

    if (left->signal < right->signal)
    {
        return -1;
    }
    if (left->signal > right->signal)
    {
        return 1;
    }
    return 0;
}

static bool kit_sortLookupTable(Kit_t *kit)
{
    if (kit == NULL)
    {
        return false;
    }

    if (kit->lookupTableCount > KIT_LOOKUP_TABLE_MAX_ENTRIES)
    {
        return false;
    }

    qsort(kit->lookupTable, kit->lookupTableCount, sizeof(kit->lookupTable[0]), lookupTableEntryCompare);
    return true;
}

static bool kit_parseLookupTableArray(cJSON *array, Kit_t *kit)
{
    size_t count = 0U;
    cJSON *entry = NULL;

    if (kit == NULL || array == NULL || !cJSON_IsArray(array))
    {
        return false;
    }

    cJSON_ArrayForEach(entry, array)
    {
        cJSON *concentration = cJSON_GetObjectItem(entry, "concentration");
        cJSON *signal = cJSON_GetObjectItem(entry, "signal");

        if (!cJSON_IsNumber(concentration) || !cJSON_IsNumber(signal))
        {
            return false;
        }
        if (count >= KIT_LOOKUP_TABLE_MAX_ENTRIES)
        {
            return false;
        }

        kit->lookupTable[count].concentration = cJSON_GetNumberValue(concentration);
        kit->lookupTable[count].signal = cJSON_GetNumberValue(signal);
        count++;
    }

    kit->hasLookupTable = count > 0U;
    kit->lookupTableCount = count;
    return kit_sortLookupTable(kit);
}

static bool pathHasExtension(const char *path, const char *extension)
{
    size_t pathLength;
    size_t extensionLength;
    if (path == NULL || extension == NULL)
    {
        return false;
    }

    pathLength = strlen(path);
    extensionLength = strlen(extension);
    if (pathLength < extensionLength)
    {
        return false;
    }

    return ascii_stricmp(path + pathLength - extensionLength, extension) == 0;
}

static bool kit_lookupTableLoadJson(const char *path, Kit_t *kit)
{
    cJSON *root = NULL;
    cJSON *array = NULL;
    char *text = NULL;
    FILE *file = NULL;
    long length = 0;
    bool ok = false;

    if (path == NULL || kit == NULL)
    {
        return false;
    }

    file = fopen(path, "rb");
    if (file == NULL)
    {
        return false;
    }

    if (fseek(file, 0, SEEK_END) != 0)
    {
        goto cleanup;
    }
    length = ftell(file);
    if (length < 0)
    {
        goto cleanup;
    }
    if (fseek(file, 0, SEEK_SET) != 0)
    {
        goto cleanup;
    }

    text = (char *)malloc((size_t)length + 1U);
    if (text == NULL)
    {
        goto cleanup;
    }
    if (fread(text, 1, (size_t)length, file) != (size_t)length)
    {
        goto cleanup;
    }
    text[length] = '\0';

    root = cJSON_Parse(text);
    if (root == NULL)
    {
        goto cleanup;
    }

    if (cJSON_IsObject(root))
    {
        array = cJSON_GetObjectItem(root, KIT_LOOKUP_TABLE_KEY);
    }
    else
    {
        array = root;
    }

    ok = kit_parseLookupTableArray(array, kit);

cleanup:
    if (root != NULL)
    {
        cJSON_Delete(root);
    }
    free(text);
    if (file != NULL)
    {
        fclose(file);
    }
    return ok;
}

static bool nextCsvCell(char **cursor, char *buffer, size_t bufferSize)
{
    size_t length = 0U;
    char *current;

    if (cursor == NULL || *cursor == NULL || buffer == NULL || bufferSize == 0U)
    {
        return false;
    }

    current = *cursor;
    while (*current != '\0' && *current != ';' && *current != '\r' && *current != '\n')
    {
        if (length + 1U < bufferSize)
        {
            buffer[length++] = *current;
        }
        current++;
    }
    buffer[length] = '\0';

    if (*current == ';')
    {
        current++;
    }
    *cursor = current;
    return true;
}

static bool kit_lookupTableLoadCsv(const char *path, Kit_t *kit)
{
    FILE *file = NULL;
    char line[1024];
    int rfuIndex = -1;
    int concentrationIndex = -1;
    size_t rowIndex = 0U;
    size_t entryCount = 0U;
    bool ok = false;

    if (path == NULL || kit == NULL)
    {
        return false;
    }

    file = fopen(path, "r");
    if (file == NULL)
    {
        return false;
    }

    while (fgets(line, sizeof(line), file) != NULL)
    {
        char *cursor = line;
        char cell[256];
        int columnIndex = 0;

        rowIndex++;
        if (rowIndex == 1U)
        {
            while (nextCsvCell(&cursor, cell, sizeof(cell)))
            {
                if (strcmp(cell, "RFU") == 0)
                {
                    rfuIndex = columnIndex;
                }
                if (strcmp(cell, "Concentration") == 0)
                {
                    concentrationIndex = columnIndex;
                }

                if (*cursor == '\r' || *cursor == '\n' || *cursor == '\0')
                {
                    break;
                }
                columnIndex++;
            }
            if (rfuIndex < 0 || concentrationIndex < 0)
            {
                goto cleanup;
            }
            continue;
        }

        if (line[0] == '\r' || line[0] == '\n' || line[0] == '\0')
        {
            continue;
        }

        {
            char rfuText[256] = "";
            char concentrationText[256] = "";
            bool sawRfu = false;
            bool sawConcentration = false;

            cursor = line;
            columnIndex = 0;
            while (nextCsvCell(&cursor, cell, sizeof(cell)))
            {
                if (columnIndex == rfuIndex)
                {
                    snprintf(rfuText, sizeof(rfuText), "%s", cell);
                    sawRfu = true;
                }
                if (columnIndex == concentrationIndex)
                {
                    snprintf(concentrationText, sizeof(concentrationText), "%s", cell);
                    sawConcentration = true;
                }

                if (*cursor == '\r' || *cursor == '\n' || *cursor == '\0')
                {
                    break;
                }
                columnIndex++;
            }

            if ((!sawRfu || rfuText[0] == '\0') && (!sawConcentration || concentrationText[0] == '\0'))
            {
                continue;
            }
            if (!sawRfu || !sawConcentration || rfuText[0] == '\0' || concentrationText[0] == '\0')
            {
                goto cleanup;
            }
            if (entryCount >= KIT_LOOKUP_TABLE_MAX_ENTRIES)
            {
                goto cleanup;
            }

            kit->lookupTable[entryCount].signal = strtod(rfuText, NULL);
            kit->lookupTable[entryCount].concentration = strtod(concentrationText, NULL);
            entryCount++;
        }
    }

    if (entryCount < 2U)
    {
        goto cleanup;
    }

    {
        double rfuStdHigh = kit->lookupTable[0].signal;
        double rfuStdLow = kit->lookupTable[1].signal;
        size_t entryIndex;

        if (rfuStdHigh == rfuStdLow)
        {
            goto cleanup;
        }

        for (entryIndex = 0U; entryIndex < entryCount; ++entryIndex)
        {
            kit->lookupTable[entryIndex].signal =
                (kit->lookupTable[entryIndex].signal - rfuStdLow) / (rfuStdHigh - rfuStdLow);
        }
    }

    kit->hasLookupTable = entryCount > 0U;
    kit->lookupTableCount = entryCount;
    ok = kit_sortLookupTable(kit);

cleanup:
    if (file != NULL)
    {
        fclose(file);
    }
    return ok;
}

Kit_t kit_default(void)
{
    Kit_t kit = {0};
    kit.fitAlgorithm = KIT_FIT_LINEAR;
    kit.k1 = 1.0;
    kit.k2 = 0.0;
    kit.k3 = 0.0;
    kit.hasLookupTable = false;
    kit.lookupTableCount = 0U;
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
    kit.fitAlgorithm = KIT_FIT_LOOKUP_TABLE;
    kit.hasStdHighTargetSignalFactor = true;
    kit.stdHighTargetSignalFactor = 0.4;
    kit.description = QUBIT_BR_DESCRIPTION;
    kit_setLookupTableEntries(&kit, QUBIT_BR_LOOKUP_TABLE, sizeof(QUBIT_BR_LOOKUP_TABLE) / sizeof(QUBIT_BR_LOOKUP_TABLE[0]));
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

bool kit_lookupTableLoad(const char *path, Kit_t *kit)
{
    if (path == NULL || kit == NULL)
    {
        return false;
    }

    if (pathHasExtension(path, ".json"))
    {
        return kit_lookupTableLoadJson(path, kit);
    }
    if (pathHasExtension(path, ".csv"))
    {
        return kit_lookupTableLoadCsv(path, kit);
    }

    return false;
}

double kit_apply(const Kit_t *kit, double interpolated, double rfu, double stdLowConcentration, double stdLowValue, double stdHighConcentration, double stdHighValue)
{
    size_t i;
    Kit_t resolved = kit != NULL ? *kit : kit_default();

    (void)stdLowConcentration;

    switch (resolved.fitAlgorithm)
    {
        case KIT_FIT_LINEAR:
            return resolved.k1 * interpolated + resolved.k2;

        case KIT_FIT_LOOKUP_TABLE:
        {
            double deltaSignal;
            double rfuNorm;
            const KitLookupTableEntry_t *lower;
            const KitLookupTableEntry_t *upper;
            double deltaLookupSignal;
            double fraction;
            double interpolatedConcentration;

            if (!resolved.hasLookupTable || resolved.lookupTableCount == 0U)
            {
                return NAN;
            }
            if (resolved.lookupTableCount == 1U)
            {
                return resolved.lookupTable[0].concentration;
            }

            deltaSignal = stdHighValue - stdLowValue;
            if (deltaSignal == 0.0)
            {
                return NAN;
            }

            rfuNorm = (rfu - stdLowValue) / deltaSignal;
            lower = &resolved.lookupTable[0];
            upper = &resolved.lookupTable[1];

            for (i = 0U; i + 1U < resolved.lookupTableCount; i++)
            {
                lower = &resolved.lookupTable[i];
                upper = &resolved.lookupTable[i + 1U];
                if (rfuNorm <= upper->signal)
                {
                    break;
                }
            }

            deltaLookupSignal = upper->signal - lower->signal;
            if (deltaLookupSignal == 0.0)
            {
                return NAN;
            }

            fraction = (rfuNorm - lower->signal) / deltaLookupSignal;
            interpolatedConcentration = lower->concentration + fraction * (upper->concentration - lower->concentration);
            return interpolatedConcentration * resolved.k1 + resolved.k2;
        }

        default:
            return interpolated;
    }
}

cJSON * kit_toJson(const Kit_t *kit)
{
    size_t i;
    Kit_t resolved = kit != NULL ? *kit : kit_default();
    cJSON *obj = cJSON_CreateObject();

    cJSON_AddNumberToObject(obj, KIT_FIT_ALGORITHM_KEY, resolved.fitAlgorithm);
    cJSON_AddNumberToObject(obj, KIT_K1_KEY, resolved.k1);
    cJSON_AddNumberToObject(obj, KIT_K2_KEY, resolved.k2);
    cJSON_AddNumberToObject(obj, KIT_K3_KEY, resolved.k3);
    if (resolved.hasLookupTable)
    {
        cJSON *lookupTable = cJSON_CreateArray();
        for (i = 0U; i < resolved.lookupTableCount; i++)
        {
            cJSON *entry = cJSON_CreateObject();
            cJSON_AddNumberToObject(entry, "concentration", resolved.lookupTable[i].concentration);
            cJSON_AddNumberToObject(entry, "signal", resolved.lookupTable[i].signal);
            cJSON_AddItemToArray(lookupTable, entry);
        }
        cJSON_AddItemToObject(obj, KIT_LOOKUP_TABLE_KEY, lookupTable);
    }
    else
    {
        cJSON_AddNullToObject(obj, KIT_LOOKUP_TABLE_KEY);
    }
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
    cJSON *fitAlgorithm;

    if (kit == NULL)
    {
        return false;
    }

    if (obj == NULL)
    {
        *kit = kit_default();
        return true;
    }

    fitAlgorithm = cJSON_GetObjectItem(obj, KIT_FIT_ALGORITHM_KEY);
    if (fitAlgorithm == NULL)
    {
        return false;
    }

    *kit = kit_default();
    kit->fitAlgorithm = (KitFitAlgorithm_t)cJSON_GetNumberValue(fitAlgorithm);

    {
        cJSON *k1 = cJSON_GetObjectItem(obj, KIT_K1_KEY);
        if (k1 != NULL)
        {
            kit->k1 = cJSON_GetNumberValue(k1);
        }
    }

    {
        cJSON *k2 = cJSON_GetObjectItem(obj, KIT_K2_KEY);
        if (k2 != NULL)
        {
            kit->k2 = cJSON_GetNumberValue(k2);
        }
    }

    {
        cJSON *k3 = cJSON_GetObjectItem(obj, KIT_K3_KEY);
        if (k3 != NULL)
        {
            kit->k3 = cJSON_GetNumberValue(k3);
        }
    }

    {
        cJSON *lookupTable = cJSON_GetObjectItem(obj, KIT_LOOKUP_TABLE_KEY);
        if (lookupTable != NULL && !cJSON_IsNull(lookupTable))
        {
            if (!kit_parseLookupTableArray(lookupTable, kit))
            {
                return false;
            }
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

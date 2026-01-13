#pragma once

#include "cJSON.h"
#include "evifluor.h"

/**
 * @brief Loads a JSON document from disk.
 *
 * @param file Path to the JSON file.
 * @return Pointer to a cJSON tree owned by the caller, or NULL on failure.
 */
DLLEXPORT cJSON *json_loadFromFile(const char *file);

/**
 * @brief Saves a JSON document to disk.
 *
 * @param file Destination file path.
 * @param json Document to persist; ownership remains with the caller.
 */
DLLEXPORT void json_saveToFile(const char* file, cJSON* json);

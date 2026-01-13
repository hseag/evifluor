// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

/** @name Top-level JSON members */
#define DICT_MEASUREMENTS    "measurements"    /**< Array with stored measurements. */
#define DICT_SERIALNUMBER    "serialnumber"    /**< Device serial number field. */
#define DICT_FIRMWAREVERSION "firmwareVersion" /**< Firmware version string. */

/** @name Channel properties */
#define DICT_VALUE           "value"    /**< Illuminated signal entry. */
#define DICT_LED_POWER       "ledPower" /**< Applied LED drive level entry. */
#define DICT_DARK            "dark"     /**< Dark signal entry. */

/** @name Measurement sections */
#define DICT_AIR             "air"       /**< Reference/air measurement group. */
#define DICT_SAMPLE          "sample"    /**< Sample measurement group. */
#define DICT_DATE_TIME       "date_time" /**< ISO-8601 timestamp field. */
#define DICT_LOGGING         "logging"   /**< Optional logging messages array. */

/** @name Human-friendly labels used for reports */
#define DICT_AIR_DARK          DICT_AIR    " " DICT_DARK
#define DICT_AIR_VALUE         DICT_AIR    " " DICT_VALUE
#define DICT_AIR_LED_POWER     DICT_AIR    " " DICT_LED_POWER
#define DICT_SAMPLE_DARK       DICT_SAMPLE " " DICT_DARK
#define DICT_SAMPLE_VALUE      DICT_SAMPLE " " DICT_VALUE
#define DICT_SAMPLE_LED_POWER  DICT_SAMPLE " " DICT_LED_POWER

/** @name Aggregated results */
#define DICT_VALUES          "values"  /**< Container for multiple derived values. */
#define DICT_COMMENT         "comment" /**< Free-form user comment. */
#define DICT_ERRORS          "errors"  /**< Diagnostics collected during processing. */

/** @name Calculated result fields */
#define DICT_CALCULATED      "results"       /**< Root node for calculated values. */
#define DICT_CONCENTRATION   "concentration" /**< Calculated concentration entry. */

#include "cJSON.h"
#include "evifluor.h"

#define DICT_MEASUREMENTS    "measurements"
#define DICT_SERIALNUMBER    "serialnumber"
#define DICT_FIRMWAREVERSION "firmwareVersion"

#define DICT_VALUE           "value"
#define DICT_LED_POWER       "ledPower"
#define DICT_DARK            "dark"

#define DICT_AIR             "air"
#define DICT_SAMPLE          "sample"

#define DICT_AIR_DARK          DICT_AIR    " " DICT_DARK
#define DICT_AIR_VALUE         DICT_AIR    " " DICT_VALUE
#define DICT_AIR_LED_POWER     DICT_AIR    " " DICT_LED_POWER
#define DICT_SAMPLE_DARK       DICT_SAMPLE " " DICT_DARK
#define DICT_SAMPLE_VALUE      DICT_SAMPLE " " DICT_VALUE
#define DICT_SAMPLE_LED_POWER  DICT_SAMPLE " " DICT_LED_POWER

#define DICT_VALUES          "values"
#define DICT_COMMENT         "comment"

#define DICT_CALCULATED      "calculated"
#define DICT_CONCENTRATION   "concentration"

cJSON *jsonLoad(char *file);
void jsonSave(char* file, cJSON* json);

cJSON* singleMeasurmentToJson(SingleMeasurement_t * measurement);

#pragma once

enum EviFluoIndices
{
  INDEX_LASTMEASUREMENTCOUNT                  = 10,
  INDEX_AUTOGAIN_DELTA                        = 11,
  INDEX_CUVETTE_EMPTY_DELTA                   = 12,
  INDEX_CUVETTE_EMPTY_LED_POWER               = 14,
  INDEX_CURRENT_LED470_POWER                  = 15,
  INDEX_CURRENT_LED470_POWER_MIN              = 16,
  INDEX_CURRENT_LED470_POWER_MAX              = 17,
  INDEX_CURRENT_LED625_POWER_MIN              = 18,
  INDEX_CURRENT_LED625_POWER_MAX              = 19,
  INDEX_CURRENT_LED625_POWER                  = 20,
  INDEX_SENSOR_LED                            = 21,

  
  //USED ONLY FROM DILBERT
  INDEX_AUTOGAIN_LED_POWER                    = 1000,
  INDEX_AUTOGAIN_VALID                        = 1001,
  INDEX_AUTOGAIN_LEVEL                        = 1002,
  INDEX_CUVETTE_EMPTY_DELTA_VALUE             = 1003,
  INDEX_CUVETTE_EMPTY_IS_EMPTY                = 1004,
};

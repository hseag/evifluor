# Usage
1. Pick up a tip with your liquid handler
2. Aspirate at least 11 &#956;l of sample
3. Pick up a cuvette
4. Move the cuvette over the eviFluor module
5. Execute `evifluor baseline`
6. Insert the cuvette into the eviFluor module
7. Execute `evifluor measure --first-air` if it is the first air measurement. If not execute `evifluor measure`
8. Dispense approximately 10.5 &#956;l sample into the cuvette
9. Execute `evifluor measure --first-sample`if it is the first sample measurement. If not execute `evifluor measure`
10. Move the cuvette out off the eviFluor module
11. Execute `evifluor save data.json`
12. Dispose the tip with attached cuvette
13. Repeat steps 1-13 until all samples are processed

The first sample must be standard high and the second sample must be standard low.

With `evifluor data calculate 0 CONCENTRATION_HIGH data.json` add the caclculated values to the data.json. Replace CONCENTRATION_HIGH with the correct value.

# Help
```
Usage: evifluor [OPTIONS] COMMAND [ARGUMENTS]
Commands:
  baseline            : starts a new series of measurements
  command COMMAND     : executes a command e.g evifluor.exe command "V 0" returns the value at index 0
  data                : handels data in a data file
  empty               : checks if the cuvette guide is empty
  export              : exports json data files as csv files
  fwupdate FILE       : loads a new firmware
  get INDEX           : get a value from the device
  help COMMAND        : prints a detailed help
  measure             : starts a measurement and return the values
  save                : save the last measurement(s)
  selftest            : executes an internal selftest
  set INDEX VALUE     : set a value in the device
  version             : returns the version
Options:
  --verbose           : prints debug info
  --help -h           : show this help and exit
  --device            : use the given device, if omitted the CLI searchs for a device
  --use-checksum      : use the protocol with a checksum

The commandline tool returns the following exit codes:
    0: No error.
    1: Unknown command
    2: Invalid parameter
    3: Timeout.
    4: SREC Flash write error
    5: SREC Unsupported type
    6: SREC Invalid crc
    7: SREC Invalid string
    8: Levelling failed. Cuvette holder blocked?
   10: EviFluor Module not found
   50: Unknown command line option
   51: Response error
   52: Protocol error
   53: Unknown command line argument
   55: Invalid number
   56: File not found
  100: Communication error
```
# Command Details
## Command baseline
```
Usage: evifluor baseline
  The firmware has an internal storage for up to ten measurements. The command baseline clears this storage.
```
## Command command 
```
Usage: evifluor command COMMAND
  Executes any evifluor command. Usefull for testing.
```
## Command data
```
Usage: evifluor data print FILE
  Prints the calculated values from file FILE.
Output:
  concentration comment
```
```
Usage: evifluor data calculate CONCENTRATION_LOW CONCENTRATION_HIGH FILE
  Calculates the concentration in the given file and adds the values to the file.
  CONCENTRATION_LOW is usually 0, CONCENTRATION_HIGH depends on the used kit.
  To calculate the values the first sample must be standard high and the second sample must be standard low
```
## Command empty
```
Usage: evifluor empty
  Checks if the cuvette guide is empty.
  Returns 'Empty' if the cuvette guide is empty or if not empty 'Not empty'
```
## Command export
```
  Usage: evifluor export [OPTIONS] [JSON FILE] [CSV FILE]
  Exports data from the JSON file in CSV format.
Options: 
  --delimiter-comma     : use commas as separators (Default).
  --delimiter-semicolon : use semicolons as separators.
  --delimiter-tab       : use tabs as separators.
  --mode-raw            : export single measurements.
  --mode-measurement    : export air-sample pairs (Default).
```
## Command fwupdate 
```
Usage: evifluor fwupdate SREC_FILE
  Updates the firmware.
```
## Command get
```
Usage: evifluor get INDEX
  Get a value from the device
INDEX:
   0: Firmware version
   1: Serial number
   2: Hardware type
  10: Number of internal stored last measurements
  15: Led power
  16: Led power minimum value
  17: Led power maximum value
```
## Command measure 
```
Usage: evifluor measure [OPTIONS]
  Measures and print the value to stdout.
Output (measure)    : dark sample ledPower
Output (first-air)  : min-dark min-sample min-ledPower max-dark max-sample max-ledPower 
Output (first-sampl): dark sample ledPower autogain-found autogain-ledPower
Options: 
  --measure             :  (Default).
  --first-air           :  Performs a first air measurment.
  --first-sample        :  Performs a first sample measurment (autogain).
```
## Command save
```
Usage: evifluor save [FILE] [COMMENT]
  Saves the last measurements in the given file FILE as a JSON file.
  The optional string COMMENT is added as a comment to the measurement in the JSON file.
Options: 
  --append           : append the new data at the end of the file (Default).
  --create           : create the file and add the data at the end of the file.
  --mode-raw         : append all measurments as single measurements.
  --mode-measurement : append all measurments as air-sample pairs (Default).
```
## Command selftest
```
Usage: evifluor selftest
  Executes a selftest and prints the result.
```
## Command set
```  
Usage: evifluor set INDEX VALUE
  Set a value in the device
WARNING:
  Changing a value can damage the device or lead to incorrect results!
INDEX:
   1: Serial number
   2: Hardware type
  15: Led power
```
## Command version
```  
Usage: evifluor version
  Prints the version of this tool to stdout.
```


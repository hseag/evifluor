// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>


#include "cmdget.h"
#include "cmdset.h"
#include "cmdmeasure.h"
#include "cmdbaseline.h"
#include "cmdselftest.h"
#include "cmdcommand.h"
#include "cmdfwupdate.h"
#include "cmdrun.h"
#include "cmddata.h"
#include "cmdsave.h"
#include "cmdexport.h"
#include "cmdempty.h"
#include "printerror.h"
#include <stdio.h>
#include <string.h>

#define VERSION_TOOL "0.6.0"

void help(int argcCmd, char **argvCmd)
{
	if(argvCmd == NULL)
	{
            fprintf_s(stdout, "Usage: evifluor [OPTIONS] COMMAND [ARGUMENTS]\n");
            fprintf_s(stdout, "Commands:\n");
            fprintf_s(stdout, "  baseline            : starts a new series of measurements\n");
            fprintf_s(stdout, "  command COMMAND     : executes a device command; e.g. \"evifluor.exe command \\\"V 0\\\"\" returns the value at index 0\n");
            fprintf_s(stdout, "  data                : handles data in a data file\n");
            fprintf_s(stdout, "  empty               : checks if the cuvette guide is empty\n");
            fprintf_s(stdout, "  export              : exports JSON data files as CSV files\n");
            fprintf_s(stdout, "  fwupdate FILE       : loads a new firmware\n");
            fprintf_s(stdout, "  get INDEX           : gets a value from the device\n");
            fprintf_s(stdout, "  help [COMMAND]      : prints detailed help\n");
            fprintf_s(stdout, "  measure             : starts a measurement and returns the values\n");
            fprintf_s(stdout, "  run                 : performs a guided workflow\n");
            fprintf_s(stdout, "  save                : saves the last measurement(s)\n");
            fprintf_s(stdout, "  selftest            : executes an internal self-test\n");
            fprintf_s(stdout, "  set INDEX VALUE     : sets a value in the device\n");
            fprintf_s(stdout, "  version             : returns the version\n");
            fprintf_s(stdout, "Options:\n");
            fprintf_s(stdout, "  --verbose           : prints debug info\n");
            fprintf_s(stdout, "  --help, -h          : show this help and exit\n");
            fprintf_s(stdout, "  --device DEVICE     : use the given device; if omitted, the CLI searches for a device\n");
            fprintf_s(stdout, "  --use-checksum      : use the protocol with a checksum\n");
            fprintf_s(stdout, "\n");
            fprintf_s(stdout, "The command-line tool returns the following exit codes:\n");
            fprintf_s(stdout, "    0: No error.\n");
            fprintf_s(stdout, "    1: Unknown command\n");
            fprintf_s(stdout, "    2: Invalid parameter\n");
            fprintf_s(stdout, "    3: Timeout.\n");
            fprintf_s(stdout, "    4: SREC flash write error\n");
            fprintf_s(stdout, "    5: SREC unsupported type\n");
            fprintf_s(stdout, "    6: SREC invalid CRC\n");
            fprintf_s(stdout, "    7: SREC invalid string\n");
            fprintf_s(stdout, "    8: Leveling failed. Cuvette holder blocked?\n");
            fprintf_s(stdout, "   10: EviFluor module not found\n");
            fprintf_s(stdout, "   50: Unknown command-line option\n");
            fprintf_s(stdout, "   51: Response error\n");
            fprintf_s(stdout, "   52: Protocol error\n");
            fprintf_s(stdout, "   53: Unknown command-line argument\n");
            fprintf_s(stdout, "   55: Invalid number\n");
            fprintf_s(stdout, "   56: File not found\n");
            fprintf_s(stdout, "   57: Cuvette guide not empty\n");
            fprintf_s(stdout, "  100: Communication error\n");
	}
	else
	{
		if(argcCmd == 2)
		{
			if(strcmp(argvCmd[1], "get") == 0)
			{
                fprintf_s(stdout, "Usage: evifluor get INDEX\n");
                fprintf_s(stdout, "  Get a value from the device\n");
                fprintf_s(stdout, "INDEX:\n");
                fprintf_s(stdout, "   0: Firmware version\n");
                fprintf_s(stdout, "   1: Serial number\n");
                fprintf_s(stdout, "   3: Production number\n");
                fprintf_s(stdout, "  10: Number of stored measurements\n");
				fprintf_s(stdout, "  15: LED power\n");
				fprintf_s(stdout, "  16: LED power minimum value\n");
				fprintf_s(stdout, "  17: LED power maximum value\n");
			}
			else if(strcmp(argvCmd[1], "set") == 0)
			{
                fprintf_s(stdout, "Usage: evifluor set INDEX VALUE\n");
                fprintf_s(stdout, "  Set a value on the device\n");
                fprintf_s(stdout, "WARNING:\n");
                fprintf_s(stdout, "  Changing a value can damage the device or lead to incorrect results!\n");
                fprintf_s(stdout, "INDEX:\n");
                fprintf_s(stdout, "   1: Serial number\n");
                fprintf_s(stdout, "   2: Production number\n");
				fprintf_s(stdout, "  15: LED power\n");
			}
			else if(strcmp(argvCmd[1], "save") == 0)
			{
                fprintf_s(stdout, "Usage: evifluor save [FILE] [COMMENT]\n");
                fprintf_s(stdout, "  Saves the latest measurements to FILE as a JSON file.\n");
                fprintf_s(stdout, "  The optional COMMENT string is added to the measurement in the JSON file.\n");
                fprintf_s(stdout, "Options:\n");
                fprintf_s(stdout, "  --append           : append the new data at the end of the file (default)\n");
                fprintf_s(stdout, "  --create           : create the file and append the data at the end of the file\n");
                fprintf_s(stdout, "  --mode-raw         : append all measurements as single measurements\n");
                fprintf_s(stdout, "  --mode-measurement : append all measurements as air-sample pairs (default)\n");
			}
            else if(strcmp(argvCmd[1], "data") == 0)
            {
                fprintf_s(stdout, "Usage: evifluor data print FILE\n");
                fprintf_s(stdout, "  Prints the calculated values from FILE.\n");
                fprintf_s(stdout, "Output:\n");
                fprintf_s(stdout, "  concentration comment\n");
                fprintf_s(stdout, "\n");
                fprintf_s(stdout, "Usage: evifluor data calculate CONCENTRATION_LOW CONCENTRATION_HIGH NR_OF_SAMPLES_LOW NR_OF_SAMPLES_HIGH FILE\n");
                fprintf_s(stdout, "  Calculates the concentration in the given file and adds the values to the file.\n");
                fprintf_s(stdout, "  CONCENTRATION_LOW is usually 0, CONCENTRATION_HIGH depends on the used kit.\n");
                fprintf_s(stdout, "  To calculate the values, the first NR_OF_SAMPLES_HIGH sample(s) must be standard high and the following NR_OF_SAMPLES_LOW sample(s) standard low.\n");
            }
            else if(strcmp(argvCmd[1], "export") == 0)
            {
                fprintf_s(stdout, "Usage: evifluor export [OPTIONS] [JSON FILE] [CSV FILE]\n");
                fprintf_s(stdout, "  Exports data from the JSON file to CSV format.\n");
                fprintf_s(stdout, "Options:\n");
                fprintf_s(stdout, "  --delimiter-comma     : use commas as separators (default)\n");
                fprintf_s(stdout, "  --delimiter-semicolon : use semicolons as separators\n");
                fprintf_s(stdout, "  --delimiter-tab       : use tabs as separators\n");
                fprintf_s(stdout, "  --mode-raw            : export single measurements\n");
                fprintf_s(stdout, "  --mode-measurement    : export air-sample pairs (default)\n");
            }
			else if(strcmp(argvCmd[1], "measure") == 0)
			{
                fprintf_s(stdout, "Usage: evifluor measure [OPTIONS]\n");
                fprintf_s(stdout, "  Measures and prints the value to stdout.\n");
                fprintf_s(stdout, "Output (measure)    : dark sample ledPower\n");
                fprintf_s(stdout, "Output (first-air)  : min-dark min-sample min-ledPower max-dark max-sample max-ledPower\n");
                fprintf_s(stdout, "Output (first-sample) : dark sample ledPower autogain-found autogain-ledPower\n");
                fprintf_s(stdout, "Options:\n");
                fprintf_s(stdout, "  --measure             : perform the default measurement (default)\n");
                fprintf_s(stdout, "  --first-air           : perform a first-air measurement\n");
                fprintf_s(stdout, "  --first-sample        : perform a first-sample measurement (autogain)\n");
			}
            else if(strcmp(argvCmd[1], "run") == 0)
            {
                fprintf_s(stdout, "Usage: evifluor run [OPTIONS] init NR_STD_HIGH NR_STD_LOW CONCENTRATION\n");
                fprintf_s(stdout, "  Initializes a run.\n");
                fprintf_s(stdout, "Usage: evifluor run [OPTIONS] measure [COMMENT]\n");
                fprintf_s(stdout, "  Executes a measurement.\n");
                fprintf_s(stdout, "Usage: evifluor run [OPTIONS] checkempty\n");
                fprintf_s(stdout, "  Checks if the cuvette guide is empty.\n");
                fprintf_s(stdout, "  Returns exit code 0 when the cuvette guide is empty; otherwise, the exit code is non-zero.\n");
                fprintf_s(stdout, "Usage: evifluor run [OPTIONS] export\n");
                fprintf_s(stdout, "  Exports the active run data JSON file as a CSV file with the same basename.\n");
                fprintf_s(stdout, "Options:\n");
                fprintf_s(stdout, "  --working-dir=DIR      : working directory (default: .)\n");
                fprintf_s(stdout, "  --file=FILE            : data file\n");
            }
            else if(strcmp(argvCmd[1], "baseline") == 0)
            {
                fprintf_s(stdout, "Usage: evifluor baseline\n");
                fprintf_s(stdout, "  Clears the firmware's internal storage of up to ten measurements.\n");
            }
			else if(strcmp(argvCmd[1], "version") == 0)
			{
                fprintf_s(stdout, "Usage: evifluor version\n");
                fprintf_s(stdout, "  Prints the version of this tool to stdout.\n");
			}
			else if(strcmp(argvCmd[1], "selftest") == 0)
			{
                fprintf_s(stdout, "Usage: evifluor selftest\n");
                fprintf_s(stdout, "  Executes a self-test and prints the result.\n");
			}
			else if(strcmp(argvCmd[1], "fwupdate") == 0)
            {
                fprintf_s(stdout, "Usage: evifluor fwupdate SREC_FILE\n");
                fprintf_s(stdout, "  Updates the firmware from the specified SREC file.\n");
			}
            else if(strcmp(argvCmd[1], "empty") == 0)
            {
                fprintf_s(stdout, "Usage: evifluor empty\n");
                fprintf_s(stdout, "  Checks if the cuvette guide is empty.\n");
                fprintf_s(stdout, "  Returns 'Empty' if the cuvette guide is empty; otherwise, returns 'Not empty'.\n");
            }
            else if(strcmp(argvCmd[1], "command") == 0)
			{
                fprintf_s(stdout, "Usage: evifluor command COMMAND\n");
                fprintf_s(stdout, "  Executes any EviFluor command. Useful for testing.\n");
			}
			else
            {
                fprintf_s(stdout, "No help for command '%s'\n", argvCmd[1]);
			}
		}
		else
		{
			help(0, NULL);
		}
	}
}


int main(int argc, char *argv[])
{
    Error_t ret = ERROR_EVI_OK;
	int argcCmd = argc;
	char **argvCmd = argv;
	bool options = true;
	int i = 1;
    Evi_t evifluor = {0};

	while (i < argc && options)
	{
		if (strncmp(argv[i], "--", 2) == 0 || strncmp(argv[i], "-", 1) == 0)
		{
			if (strcmp(argv[i], "--verbose") == 0)
			{
                evifluor.verbose = true;
			}
			else if (strcmp(argv[i], "--use-checksum") == 0)
			{
                evifluor.useChecksum = true;
			}
			else if (strcmp(argv[i], "--help") == 0 || strcmp(argv[i], "-h") == 0)
			{
				help(0, NULL);
                return ERROR_EVI_OK;
			}
			else if ((strcmp(argv[i], "--device") == 0) && (i + 1 < argc))
			{
				i++;
                evifluor.portName = argv[i];
			}
			else
			{
                return printError(ERROR_EVI_UNKOWN_COMMAND_LINE_OPTION, "Unknown option: %s\n", argv[i]);
			}
			i++;
		}
		else
		{
			options = false;
		}
	}

	argcCmd = argc - i;
	argvCmd = argv + i;

	if (argcCmd > 0)
	{
		if (strcmp(argvCmd[0], "get") == 0 && argcCmd == 2)
		{
            return cmdGet(&evifluor, argvCmd[1]);
		}
		else if (strcmp(argvCmd[0], "set") == 0 && argcCmd == 3)
		{
            return cmdSet(&evifluor, argvCmd[1], argvCmd[2]);
		}
        else if (strcmp(argvCmd[0], "measure") == 0 && argcCmd >= 1)
		{
            return cmdMeasure(&evifluor, argcCmd, argvCmd);
		}
		else if (strcmp(argvCmd[0], "version") == 0)
		{
            fprintf(stdout, "%s\n", VERSION_TOOL);
		}
		else if (strcmp(argvCmd[0], "selftest") == 0 && argcCmd == 1)
		{
            return cmdSelftest(&evifluor);
		}
		else if (strcmp(argvCmd[0], "fwupdate") == 0 && argcCmd == 2)
		{
            return cmdFwUpdate(&evifluor, argvCmd[1]);
		}
		else if (strcmp(argvCmd[0], "command") == 0 && argcCmd == 2)
		{
            return cmdCommand(&evifluor, argvCmd[1]);
		}
        else if (strcmp(argvCmd[0], "data") == 0)
        {
            return cmdData(&evifluor, argcCmd, argvCmd);
        }
        else if (strcmp(argvCmd[0], "save") == 0)
		{
            return cmdSave(&evifluor, argcCmd, argvCmd);
		}
        else if (strcmp(argvCmd[0], "export") == 0)
        {
            return cmdExport(&evifluor, argcCmd, argvCmd);
        }
		else if (strcmp(argvCmd[0], "baseline") == 0)
		{
            return cmdBaseline(&evifluor);
		}
        else if (strcmp(argvCmd[0], "empty") == 0)
        {
            return cmdEmpty(&evifluor);
        }
        else if (strcmp(argvCmd[0], "run") == 0)
        {
            return cmdRun(&evifluor, argcCmd, argvCmd);
        }
        else if (strcmp(argvCmd[0], "help") == 0)
		{
			help(argcCmd, argvCmd);
            return ERROR_EVI_OK;
		}
		else
		{
            return printError(ERROR_EVI_UNKOWN_COMMAND_LINE_ARGUMENT, "'%s' is not a evifluor command. See 'evifluor --help'.", argvCmd[0]);
		}
	}
	else
	{
		help(0, NULL);
	}

	return ret;
}

// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "evibase.h"
#include "eviconfig.h"
#include "crc-16-ccitt.h"
#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <windows.h>
#include <tchar.h>
#include <setupapi.h>
#include <cfgmgr32.h>
#include <initguid.h>
#include <devguid.h> 
#include <WinDef.h>
#include <stdio.h>
#include <stdarg.h>

#pragma comment(lib, "Setupapi.lib")
// This is the GUID for the USB device class
DEFINE_GUID(GUID_DEVINTERFACE_USB_DEVICE, 0xA5DCBF10L, 0x6530, 0x11D2, 0x90, 0x1F, 0x00, 0xC0, 0x4F, 0xB9, 0x51, 0xED);
DEFINE_GUID(GUID_DEVINTERFACE_MODEM, 0x2c7089aa, 0x2e0e, 0x11d1, 0xb1, 0x14, 0x00, 0xc0, 0x4f, 0xc2, 0xaa, 0xe4);

typedef struct 
{
	GUID guid;
	DWORD flags;
} SetupTokens_t;



static bool devicePortName(HDEVINFO deviceInfoSet, PSP_DEVINFO_DATA deviceInfoData, char * portName, size_t * portNameSize)
{
	bool ret = false;
    const HKEY key = SetupDiOpenDevRegKey(deviceInfoSet, deviceInfoData, DICS_FLAG_GLOBAL, 0, DIREG_DEV, KEY_READ);
    if (key == INVALID_HANDLE_VALUE)
        return false;

    static LPCSTR  keyTokens[] = {
            _T("PortName\0"),
            _T("PortNumber\0")
    };

    enum { KeyTokensCount = sizeof(keyTokens) / sizeof(keyTokens[0]) };

    for (int i = 0; i < KeyTokensCount; ++i) {
        DWORD dataType = 0;
        BYTE * outputBuffer = malloc(MAX_PATH + 1);
		memset(outputBuffer, 0, MAX_PATH + 1);
        DWORD bytesRequired = MAX_PATH;
        for (;;) 
		{
            const LONG ret = RegQueryValueEx(key, keyTokens[i], NULL, &dataType, outputBuffer, &bytesRequired);
            if (ret == ERROR_MORE_DATA) 
			{
                //outputBuffer.resize(bytesRequired / sizeof(wchar_t) + 2, 0);
                continue;
            } 
			else if (ret == ERROR_SUCCESS) 
			{
                if (dataType == REG_SZ)
				{
				    strncpy(portName, (char*)outputBuffer, *portNameSize);
				}
                else if (dataType == REG_DWORD)
				{
					DWORD * w = (DWORD *)outputBuffer;
				    sprintf(portName, "COM%lu", *w);
				}
            }
            break;
        }

        if (strlen(portName) != 0)
		{
			ret = true;
            break;
		}
    }
    RegCloseKey(key);
    return ret;
}

static char* deviceInstanceIdentifier(DEVINST deviceInstanceNumber)
{
    char * outputBuffer = malloc(MAX_DEVICE_ID_LEN + 1);
	memset(outputBuffer, 0, MAX_DEVICE_ID_LEN + 1);
    if (CM_Get_Device_ID(deviceInstanceNumber, &outputBuffer[0], MAX_DEVICE_ID_LEN, 0) != CR_SUCCESS) 
	{
        return outputBuffer;
    }
    return outputBuffer;
}

static uint16_t parseDeviceIdentifier(char *instanceIdentifier, char * identifierPrefix, int identifierSize, bool * ok)
{
	uint16_t ret = 0;
	char * s = strstr(instanceIdentifier, identifierPrefix);
	if (s != NULL) 
	{
		char *endptr;
      	ret = strtol(s + strlen(identifierPrefix), &endptr, 16);
		*ok = (endptr != (s + strlen(identifierPrefix)));
    }
	else
	{
		*ok = false;
	}
	return ret;
}

static uint16_t deviceVendorIdentifier(char * instanceIdentifier, bool * ok)
{
    static const int vendorIdentifierSize = 4;
    uint16_t result = parseDeviceIdentifier( instanceIdentifier, "VID_", vendorIdentifierSize, ok);
    if (!(*ok))
	{
        result = parseDeviceIdentifier(instanceIdentifier, "VEN_", vendorIdentifierSize, ok);
	}
    return result;
}

static uint16_t deviceProductIdentifier(char * instanceIdentifier, bool * ok)
{
    static const int vendorIdentifierSize = 4;
    uint16_t result = parseDeviceIdentifier( instanceIdentifier, "PID_", vendorIdentifierSize, ok);
    if (!(*ok))
	{
        result = parseDeviceIdentifier(instanceIdentifier, "DEV_", vendorIdentifierSize, ok);
	}
    return result;
}

Error_t eviFindDevice(char * portName, size_t * portNameSize, bool verbose)
{
	SetupTokens_t setupTokens[] = { {GUID_DEVCLASS_PORTS, DIGCF_PRESENT },
							        { GUID_DEVCLASS_MODEM, DIGCF_PRESENT },
        							{ GUID_DEVINTERFACE_COMPORT, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE },
        							{ GUID_DEVINTERFACE_MODEM, DIGCF_PRESENT | DIGCF_DEVICEINTERFACE }
									};

	int setupTokensCount = sizeof(setupTokens) / sizeof(setupTokens[0]);
	bool found = false;

	for (int i = 0; i < setupTokensCount && !found ; ++i) 
	{
		 HDEVINFO deviceInfoSet = SetupDiGetClassDevs(&setupTokens[i].guid, NULL, NULL, setupTokens[i].flags);
        if (deviceInfoSet == INVALID_HANDLE_VALUE)
		{
            return ERROR_EVI_INSTRUMENT_NOT_FOUND;
		}

        SP_DEVINFO_DATA deviceInfoData;
        memset(&deviceInfoData, 0, sizeof(deviceInfoData));
        deviceInfoData.cbSize = sizeof(deviceInfoData);

        DWORD index = 0;
        while (SetupDiEnumDeviceInfo(deviceInfoSet, index++, &deviceInfoData)) 
		{
			bool ok;
			uint16_t vid;
			uint16_t pid;
			{
				char * instanceIdentifier = deviceInstanceIdentifier(deviceInfoData.DevInst);		
				vid = deviceVendorIdentifier(instanceIdentifier, &ok);
				pid = deviceProductIdentifier(instanceIdentifier, &ok);

			   	if(verbose)
               	{
	   				fprintf(stderr, "DEVICES: %s\n", instanceIdentifier);
   				}

				free(instanceIdentifier);
			}

            if(vid == EVI_COMMON_VID && pid == EVI_COMMON_PID)
			{
				if(devicePortName(deviceInfoSet, &deviceInfoData, portName, portNameSize))
				{
				  found = true;
				  break;
				}
			}
        }
        SetupDiDestroyDeviceInfoList(deviceInfoSet);		
	}

    return found ? ERROR_EVI_OK : ERROR_EVI_INSTRUMENT_NOT_FOUND;
}

HANDLE eviPortOpen(char * portName)
{
	HANDLE hComm;
	{
		LPTSTR dn = "\\\\.\\";
		DWORD deviceSize = strlen(portName) + strlen(dn) + 1;
		LPTSTR device = HeapAlloc(GetProcessHeap(), HEAP_ZERO_MEMORY, deviceSize);
		strcat_s(device, deviceSize, dn);
		strcat_s(device, deviceSize, portName);

		hComm = CreateFile(device,						 // port name
						   GENERIC_READ | GENERIC_WRITE, // Read/Write
						   0,							 // No Sharing
						   NULL,						 // No Security
						   OPEN_EXISTING,				 // Open existing port only
						   0,							 // Non Overlapped I/O
						   NULL);						 // Null for Comm Devices

		HeapFree(GetProcessHeap(), 0, device);
	}

	if (hComm == INVALID_HANDLE_VALUE)
	{
		fprintf(stderr, "could not open port %s\n", portName);
		return INVALID_HANDLE_VALUE;
	}

	BOOL success = FlushFileBuffers(hComm);
	if (!success)
	{
		fprintf(stderr, "could not flush buffers\n");
		CloseHandle(hComm);
		return INVALID_HANDLE_VALUE;
	}

	// Configure read and write operations to time out after 100 ms.
	COMMTIMEOUTS timeouts = {0};
	timeouts.ReadIntervalTimeout = 0;
	timeouts.ReadTotalTimeoutConstant = 1;
	timeouts.ReadTotalTimeoutMultiplier = 0;
	timeouts.WriteTotalTimeoutConstant = 1;
	timeouts.WriteTotalTimeoutMultiplier = 0;

	success = SetCommTimeouts(hComm, &timeouts);
	if (!success)
	{
		fprintf(stderr, "could not timeouts\n");
		CloseHandle(hComm);
		return INVALID_HANDLE_VALUE;
	}

	// Set the baud rate and other options.
	DCB state = {0};
	state.DCBlength = sizeof(DCB);
    state.BaudRate = CBR_115200;
	state.ByteSize = 8;
	state.Parity = NOPARITY;
	state.StopBits = ONESTOPBIT;
	success = SetCommState(hComm, &state);
	if (!success)
	{
		fprintf(stderr, "could not set serial settings\n");
		CloseHandle(hComm);
		return INVALID_HANDLE_VALUE;
	}

	return hComm;
}

void eviPortClose(HANDLE hComm)
{
	if (hComm != INVALID_HANDLE_VALUE)
	{
		CloseHandle(hComm); // Closing the Serial Port
	}
}

bool eviPortWrite(HANDLE hComm, LPTSTR buffer, bool verbose)
{
	DWORD written;
	DWORD size = strlen(buffer);

   if(verbose)
   {
	fprintf(stderr, "TX: %s\n", buffer);
   }

	BOOL success = WriteFile(hComm, buffer, size, &written, NULL);
	if (!success)
	{
		fprintf(stderr, "could not write to port\n");
		return false;
	}
	if (written != size)
	{
    	fprintf(stderr, "could not all bytes to port\n");
		return false;
	}
	return true;
}

uint32_t eviPortRead(HANDLE hComm, LPTSTR buffer, size_t size, bool verbose)
{
	DWORD received;
	DWORD count = 0;
    char rx[EVI_MAX_LINE_LENGTH];
	bool waitForStart = true;
	bool done = false;
	bool useChecksum = false;
	int checkSumSeparator = -1;

	do
	{
        memset(rx, 0, EVI_MAX_LINE_LENGTH);
        BOOL success = ReadFile(hComm, rx, EVI_MAX_LINE_LENGTH, &received, NULL);
		if (!success)
		{
			fprintf(stderr, "could not read from port\n");
			return -1;
		}

        if(verbose && received > 0)
        {
	      fprintf(stderr, "RX: %s\n", rx);
        }		

		for (DWORD i = 0; i < received && !done; i++)
		{
			if (waitForStart)
			{
                if (rx[i] == EVI_START_NO_CHK || rx[i] == EVI_START_WITH_CHK)
				{
					waitForStart = false;
                    if(rx[i] == EVI_START_WITH_CHK)
					{
						useChecksum = true;
					}
				}
			}
			else
			{
                if (rx[i] == EVI_STOP1 || rx[i] == EVI_STOP2)
				{
					done = true;
					buffer[count] = 0;
				}
				else
				{
     			    buffer[count] = rx[i];
                    if(buffer[count] == EVI_CHECKSUM_SEPARATOR)
					{
						checkSumSeparator = count;
					}
					count++;
				}
			}
		}
	} while (!done);

    if(useChecksum)
	{
		crc_t crcReceived;
		crc_t crc = crc_init();
		crc = crc_update(crc, buffer, checkSumSeparator);
		crc = crc_finalize(crc);
		crcReceived = atoi(buffer+checkSumSeparator+1);
		if(crc == crcReceived)
		{
          buffer[checkSumSeparator] = 0;
		}
		else
		{
			fprintf(stderr, "CRC differ: received message %s, calculated crc=%i", buffer, crcReceived);
			return 0;
		}
	}

	return count;
}

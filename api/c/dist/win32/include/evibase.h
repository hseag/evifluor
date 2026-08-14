// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once
#include "commonerror.h"
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

#if defined(_WIN64) || defined(_WIN32)
#include <winsock2.h>
#include <ws2tcpip.h>
#include <windows.h>
#define DLLEXPORT __declspec(dllexport)

typedef struct
{
    HANDLE handle;
    bool valid;
    bool isSocket;
    WSADATA wsa_data;
    SOCKET socket;
} EVI_HANDLE;

#else
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <ctype.h>
#include <stdarg.h>
#define DLLEXPORT
typedef int EVI_HANDLE;
typedef int errno_t;
typedef size_t rsize_t;
#define INVALID_HANDLE_VALUE -1
extern errno_t strncat_s(char *restrict dest, rsize_t destsz, const char *restrict src, rsize_t count);
extern errno_t strncpy_s(char *restrict dest, rsize_t destsz, const char *restrict src, rsize_t count);
extern errno_t strcpy_s(char *restrict dest, rsize_t destsz, const char *restrict src);
extern int fprintf_s(FILE *stream, const char *format, ...);
extern int sprintf_s(char *str, size_t snprintf, const char *format, ...);
extern void Sleep(uint32_t dwMilliseconds);
#endif

#define EVI_MAX_LINE_LENGTH 255
#define EVI_MAX_ARGS 20
#define EVI_START_NO_CHK ':'
#define EVI_START_WITH_CHK ';'
#define EVI_CHECKSUM_SEPARATOR '@'
#define EVI_STOP1 '\n'
#define EVI_STOP2 '\r'

/**
 * @struct EvieResponse_t
 * @brief Represents a response from an Evi command.
 *
 * This structure holds the response data, including command arguments and output.
 */
typedef struct
{
    uint32_t argc; /**< Number of arguments in the response. */
    char *argv[EVI_MAX_ARGS]; /**< Array of argument strings. */
    char response[EVI_MAX_LINE_LENGTH]; /**< Response message. */    
} EvieResponse_t;

/**
 * @struct Evi_t
 * @brief Represents an Evi device configuration.
 *
 * This structure stores configuration parameters for communicating with an Evi device.
 */
typedef struct
{
    bool verbose; /**< Enables verbose output for debugging. */
    char *portName; /**< Name of the communication port. */
    bool useChecksum; /**< Whether to use checksum validation. */
} Evi_t;

/**
 * @brief Finds an Evi device connected to a port.
 *
 * @param portName Buffer to store the detected port name.
 * @param portNameSize Pointer to the size of the port name buffer.
 * @param verbose Whether to enable verbose output.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviFindDevice(char *portName, size_t *portNameSize, bool verbose);

/**
 * @brief Creates a new EvieResponse_t structure.
 * @see eviFreeResponse()
 * @return Pointer to the newly allocated EvieResponse_t structure.
 */
DLLEXPORT EvieResponse_t *eviCreateResponse();

/**
 * @brief Frees memory allocated for an EvieResponse_t structure.
 *
 * @param response Pointer to the EvieResponse_t structure to be freed.
 */
DLLEXPORT void eviFreeResponse(EvieResponse_t *response);

/**
 * @brief Sends a command to the Evi device and stores the response.
 *
 * @param self Pointer to the Evi_t structure.
 * @param command The command to be sent.
 * @param response Pointer to an EvieResponse_t structure to store the response.
 * @return An error code indicating the result of the command execution.
 */
DLLEXPORT Error_t eviCommand(Evi_t *self, const char *command, EvieResponse_t *response);

/**
 * @brief Handles a command response without returning a value.
 *
 * @param response Pointer to the response structure.
 * @param user User-defined data.
 * @return An error code indicating the result of execution.
 */
Error_t eviNoReturn_(EvieResponse_t *response, void *user);

/**
 * @brief Executes a command with a custom response handler.
 *
 * @param self Pointer to the Evi_t structure.
 * @param cmd The command to be executed.
 * @param execute Function pointer to the command execution handler.
 * @param user User-defined data passed to the handler.
 * @return An error code indicating the result of execution.
 */
Error_t eviExecute(Evi_t * self, char * cmd, Error_t(execute)(EvieResponse_t *response, void *user), void *user);

/**
 * @brief Retrieves a value from the Evi device.
 *
 * @param self Pointer to the Evi_t structure.
 * @param index Index of the value to retrieve.
 * @param value Buffer to store the retrieved value.
 * @param valueSize Size of the value buffer.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviGet(Evi_t *self, uint32_t index, char *value, size_t valueSize);

/**
 * @brief Sets a value on the Evi device.
 *
 * @param self Pointer to the Evi_t structure.
 * @param index Index of the value to set.
 * @param value The new value to be set.
 * @return An error code indicating the result of the operation.
 */
DLLEXPORT Error_t eviSet(Evi_t *self, uint32_t index, const char *value);

DLLEXPORT Error_t eviLogging(Evi_t *self, char *line, size_t length);

/**
 * @brief Performs a self-test on the Evi device.
 *
 * @param self Pointer to the Evi_t structure.
 * @param result Pointer to store the self-test result.
 * @return An error code indicating the result of the self-test.
 */
DLLEXPORT Error_t eviSelftest(Evi_t *self, uint32_t *result);

/**
 * @brief Performs a firmware update on the Evi device.
 *
 * @param self Pointer to the Evi_t structure.
 * @param file Path to the firmware update file.
 * @return An error code indicating the result of the update process.
 */
DLLEXPORT Error_t eviFwUpdate(Evi_t *self, const char *file);

/**
 * @brief Converts an error code into a human-readable string.
 *
 * @param e The error code.
 * @return A string representation of the error code.
 */
DLLEXPORT const char *eviError2String(Error_t e);

/**
 * @brief Retrieves the version of the Evi software.
 *
 * @return A string containing the software version.
 */
DLLEXPORT const char *eviVersion();

/**
 * @brief Opens a communication port for the Evi device.
 *
 * @param portName Name of the port to open.
 * @return A handle to the opened communication port.
 */
EVI_HANDLE eviPortOpen(char *portName);

/**
 * @brief Closes an open communication port.
 *
 * @param hComm Handle to the communication port.
 */
void eviPortClose(EVI_HANDLE hComm);

/**
 * @brief Writes data to the communication port.
 *
 * @param hComm Handle to the communication port.
 * @param buffer Data buffer to be written.
 * @param verbose Whether to enable verbose output.
 * @return True if the write operation was successful, otherwise false.
 */
bool eviPortWrite(EVI_HANDLE hComm, char *buffer, bool verbose);

/**
 * @brief Reads data from the communication port.
 *
 * @param hComm Handle to the communication port.
 * @param buffer Buffer to store the received data.
 * @param size Maximum number of bytes to read.
 * @param verbose Whether to enable verbose output.
 * @return The number of bytes read from the port.
 */
uint32_t eviPortRead(EVI_HANDLE hComm, char *buffer, size_t size, bool verbose);

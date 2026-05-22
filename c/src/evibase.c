// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "evibase.h"
#include "crc-16-ccitt.h"
#include <stdio.h>
#include <stdint.h>
#include <stdio.h>
#include <stdarg.h>

#define VERSION_DLL "0.2.0"

typedef struct
{
    char * value;
    size_t length;
} UserGet;

typedef struct
{
    uint32_t * result;
} UserSelftest;

typedef struct
{
    char * line;
    size_t length;
} UserLogging;

const char * eviError2String(Error_t e)
{
    switch(e)
    {
    case ERROR_EVI_OK:
        return "OK";
    case ERROR_EVI_UNKNOWN_COMMAND:
        return "Unknown command";
    case ERROR_EVI_INVALID_PARAMETER:
        return "Invalid parameter";
    case ERROR_EVI_TIMEOUT:
        return "Timeout";
    case ERROR_EVI_SREC_FLASH_WRITE_ERROR:
        return "SREC Flash write error";
    case ERROR_EVI_SREC_UNSUPPORTED_TYPE:
        return "SREC Unsupported type";
    case ERROR_EVI_SREC_INVALID_CRC:
        return "SREC Invalid crc";
    case ERROR_EVI_SREC_INVALID_STRING:
        return "SREC Invalid string";
    case ERROR_EVI_INSTRUMENT_NOT_FOUND:
        return "Module not found";
    case ERROR_EVI_FILE_NOT_FOUND:
        return "File not found";
    case ERROR_EVI_UNKOWN_COMMAND_LINE_ARGUMENT:
        return "Unknown command line argument";
    default:
        return "?";
    }
}

EvieResponse_t *eviCreateResponse()
{
    EvieResponse_t *response = (EvieResponse_t *)calloc(1, sizeof(EvieResponse_t));
    return response;
}

void eviFreeResponse(EvieResponse_t *response)
{
    free(response);
}

Error_t eviCommandComm(Evi_t *self, EVI_HANDLE hComm, const char * command, EvieResponse_t *response)
{
    Error_t ret = ERROR_EVI_OK;

    uint32_t txSize = EVI_MAX_LINE_LENGTH;
    char * tx = (char *)calloc(1, txSize);
    char s[20] = {0};
    if(self->useChecksum)
    {
        s[0] = EVI_START_WITH_CHK;
        strncat_s(tx, txSize, s, 1);
        strncat_s(tx, txSize, command, strlen(command));
        s[0] = EVI_CHECKSUM_SEPARATOR;
        strncat_s(tx, txSize, s, 1);
        crc_t crc = crc_init();
        crc = crc_update(crc, command, strlen(command));
        crc = crc_finalize(crc);
        snprintf(s, sizeof(s), "%d", (uint32_t)crc);
        strncat_s(tx, txSize, s, strlen(s));
    }
    else
    {
        s[0] = EVI_START_NO_CHK;
        strncat_s(tx, txSize, s, 1);
        strncat_s(tx, txSize, command, strlen(command));
    }
    strncat_s(tx, txSize, "\n", 1);

    eviPortWrite(hComm, tx, self->verbose);
    if (eviPortRead(hComm, response->response, EVI_MAX_LINE_LENGTH, self->verbose) > 0)
    {
        for (int i = 0; i < EVI_MAX_ARGS; i++)
        {
            response->argv[i] = 0;
        }
        response->argc = 0;
        int i = 0;
        int inQuotes = 0;
        char quoteChar = 0;
        bool inToken = false;
        char *d = response->response;
        while ((d[i] != '\0') && (i < EVI_MAX_LINE_LENGTH) && (response->argc < EVI_MAX_ARGS))
        {
            if (!inQuotes && (d[i] == '\'' || d[i] == '"'))
            {
                inQuotes = 1;
                quoteChar = d[i];
                response->argv[response->argc++] = &d[i + 1];  // Start after the opening quote
                inToken = true;
            }
            else if (inQuotes && d[i] == quoteChar)
            {
                d[i] = '\0';  // Terminate the quoted string
                inQuotes = 0;
                inToken = false;
            }
            else if (!inQuotes && isspace(d[i]))
            {
                d[i] = '\0';
                inToken = false;
            }
            else if (!inQuotes && !inToken)
            {
                response->argv[response->argc++] = &d[i];
                inToken = true;
            }
            i++;
        }
        ret = ERROR_EVI_OK;

    }
    else
    {
        ret = ERROR_EVI_INSTRUMENT_NOT_FOUND;
    }

    free(tx);
    return ret;
}

Error_t eviCommand(Evi_t *self, const char * command, EvieResponse_t *response)
{
    char portNameBuffer[1024];
    size_t portNameBufferSize = sizeof(portNameBuffer);

    Error_t ret = ERROR_EVI_OK;
    if (self->portName)
    {
        strcpy_s(portNameBuffer, portNameBufferSize, self->portName);
    }
    else
    {
        ret = eviFindDevice(portNameBuffer, &portNameBufferSize, self->verbose);
    }

    if (ret == ERROR_EVI_OK)
    {
        EVI_HANDLE hComm = eviPortOpen(portNameBuffer);
        ret = eviCommandComm(self, hComm, command, response);
        eviPortClose(hComm);
    }
    else
    {
        ret = ERROR_EVI_INSTRUMENT_NOT_FOUND;
    }
    return ret;
}

Error_t eviExecute(Evi_t * self, char * cmd, Error_t(execute)(EvieResponse_t *response, void *user), void *user)
{
    EvieResponse_t *response = eviCreateResponse();
    Error_t ret = eviCommand(self, cmd, response);
    if (ret == ERROR_EVI_OK)
    {
        if (strncmp(response->argv[0], cmd, 1) == 0)
        {
            ret = execute(response, user);
        }
        else
        {
            if(response->argc == 2 && strncmp(response->argv[0], "E", 1) == 0)
            {
                ret = atoi(response->argv[1]);
            }
            else
            {
                ret = ERROR_EVI_RESPONSE_ERROR;
            }
        }
    }
    eviFreeResponse(response);
    return ret;
}

Error_t eviNoReturn_(EvieResponse_t *response, void *user)
{
    if (response->argc == 1)
    {
        return ERROR_EVI_OK;
    }
    else
    {
        return ERROR_EVI_PROTOCOL_ERROR;
    }
}


Error_t eviGet_(EvieResponse_t *response, void *user)
{
    UserGet *u = (UserGet *)user;
    if (response->argc == 2)
    {
        strncpy_s(u->value, u->length, response->argv[1], u->length);
        return ERROR_EVI_OK;
    }
    else
    {
        return ERROR_EVI_PROTOCOL_ERROR;
    }
}

Error_t eviGet(Evi_t * self, uint32_t index, char * value, size_t valueSize)
{
    char cmd[EVI_MAX_LINE_LENGTH];
    UserGet user = { 0 };
    user.value = value;
    user.length = valueSize;
    sprintf_s(cmd, EVI_MAX_LINE_LENGTH, "V %i", index);
    return eviExecute(self, cmd, eviGet_, &user);
}

Error_t eviSet(Evi_t * self, uint32_t index, const char * value)
{
    char cmd[EVI_MAX_LINE_LENGTH];
    sprintf_s(cmd, EVI_MAX_LINE_LENGTH, "V %i %s", index, value);
    return eviExecute(self, cmd, eviNoReturn_, 0);
}

Error_t eviLogging_(EvieResponse_t *response, void *user)
{
    UserLogging *u = (UserLogging *)user;
    if (response->argc == 2)
    {
        strncpy_s(u->line, u->length, response->argv[1], u->length);
        return ERROR_EVI_OK;
    }
    else
    {
        return ERROR_EVI_PROTOCOL_ERROR;
    }
}

Error_t eviLogging(Evi_t *self, char *line, size_t length)
{
    UserLogging user = { 0 };
    user.length = length;
    user.line = line;

    char cmd[EVI_MAX_LINE_LENGTH];
    sprintf_s(cmd, EVI_MAX_LINE_LENGTH, "Q");
    return eviExecute(self, cmd, eviLogging_, &user);
}

Error_t eviSelftest_(EvieResponse_t *response, void *user)
{
    UserSelftest *u = (UserSelftest *)user;
    if (response->argc == 2)
    {
        *(u->result)    = strtoul(response->argv[1], 0, 10);
        return ERROR_EVI_OK;
    }
    else
    {
        return ERROR_EVI_PROTOCOL_ERROR;
    }
}

Error_t eviSelftest(Evi_t * self, uint32_t * result)
{
    UserSelftest user = {.result = result};
    return eviExecute(self, "Y", eviSelftest_, &user);
}

static int getlineInternal(char **lineptr, size_t *n, FILE *stream) {
    char *bufptr = NULL;
    char *p = bufptr;
    size_t size;
    int c;

    if (lineptr == NULL) {
        return -1;
    }
    if (stream == NULL) {
        return -1;
    }
    if (n == NULL) {
        return -1;
    }
    bufptr = *lineptr;
    size = *n;

    c = fgetc(stream);
    if (c == EOF) {
        return -1;
    }
    if (bufptr == NULL) {
        bufptr = malloc(128);
        if (bufptr == NULL) {
            return -1;
        }
        size = 128;
    }
    p = bufptr;
    while(c != EOF) {
        if ((p - bufptr) > (size - 1)) {
            size = size + 128;
            bufptr = realloc(bufptr, size);
            if (bufptr == NULL) {
                return -1;
            }
        }
        *p++ = c;
        if (c == '\n') {
            break;
        }
        c = fgetc(stream);
    }

    *p++ = '\0';
    *lineptr = bufptr;
    *n = size;

    return p - bufptr - 1;
}

Error_t eviFwUpdate(Evi_t * self, const char * file)
{
    Error_t ret = ERROR_EVI_OK;
    FILE * f = fopen(file, "r");
    if(f != NULL)
    {
        size_t n;
        char * line = NULL;
        int length = 0;
        Error_t ret;
        char cmd[255];
        char portNameBuffer[1024];
        size_t portNameBufferSize = sizeof(portNameBuffer);
        
        if(self->portName == 0)
        {
            ret = eviFindDevice(portNameBuffer, &portNameBufferSize, self->verbose);
            if(ret != ERROR_EVI_OK)
            {
                fclose(f);
                return ret;
            }
        }
        else
        {
            strcpy_s(portNameBuffer, portNameBufferSize, self->portName);
        }

        EvieResponse_t *response = eviCreateResponse();
        EVI_HANDLE hComm = eviPortOpen(portNameBuffer);
        ret = eviCommandComm(self, hComm, "F", response);
        do
        {
            length = getlineInternal(&line, &n, f);
            if(length != -1)
            {
                snprintf(cmd, sizeof(cmd), "S %s", line);
                ret = eviCommandComm(self, hComm, cmd, response);
                if(ret != ERROR_EVI_OK)
                {
                    return ret;
                }
            }
        }
        while(length != -1 && ret == ERROR_EVI_OK);

        ret = eviCommandComm(self, hComm, "R", response);
        if(ret != ERROR_EVI_OK)
        {
            return ret;
        }

        Sleep(30000);

        free(line);
        fclose(f);
        eviFreeResponse(response);
        eviPortClose(hComm);
    }
    else
    {
        ret = ERROR_EVI_FILE_NOT_FOUND;
    }

    return ret;
}

const char * eviVersion()
{
    return VERSION_DLL;
}


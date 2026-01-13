// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "helpers.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <time.h>

char * malloc_vprintf(const char * fmt, va_list ap)
{
    int needed;
    va_list args_copy;
    va_copy(args_copy, ap);
    needed = vsnprintf(NULL, 0, fmt, args_copy);
    va_end(args_copy);

    if(needed < 0)
    {
        return NULL;
    }
    else
    {
        needed++;
    }

    char *msg = (char *)malloc(needed);
    if (!msg)
    {
        return NULL;
    }
    (void)vsnprintf(msg, needed, fmt, ap);
    va_end(ap);

    return msg;
}

char * malloc_printf(const char * fmt, ...)
{
    int needed;
    va_list args;
    va_start(args, fmt);
    va_list args_copy;
    va_copy(args_copy, args);
    needed = vsnprintf(NULL, 0, fmt, args_copy);
    va_end(args_copy);

    if(needed < 0)
    {
        return NULL;
    }
    else
    {
        needed++;
    }

    char *msg = (char *)malloc(needed);
    if (!msg)
    {
        va_end(args);
        return NULL;
    }
    (void)vsnprintf(msg, needed, fmt, args);
    va_end(args);

    return msg;
}

char * malloc_timeStamp(TimeStampType_t timeStampType)
{
    char * ret = NULL;
    char buffer[30];
    time_t now = time(NULL);
    struct tm *t = localtime(&now);
    switch(timeStampType)
    {
    case TimeStampTypeFile:
        strftime(buffer, sizeof(buffer)-1, "%Y_%m_%d_%H_%M_%S", t);
        ret = strdup(buffer);
        break;

    case TimeStampTypeISO8601:
        strftime(buffer, sizeof(buffer)-1, "%Y-%m-%dT%H:%M:%SZ", t);
        ret = strdup(buffer);
        break;
    }
    return ret;
}

char *malloc_replace_suffix(const char *filename, const char *new_suffix) {
    // Find the last dot in the filename
    const char *dot = strrchr(filename, '.');
    size_t base_len;
    if (dot) {
        base_len = (size_t)(dot - filename);  // length before '.'
    } else {
        base_len = strlen(filename);          // no suffix found
    }

    // Allocate enough memory for base + '.' + new_suffix + '\0'
    size_t new_len = base_len + 1 + strlen(new_suffix) + 1;
    char *new_name = malloc(new_len);
    if (!new_name) {
        return NULL;
    }

    // Copy the base name and append new suffix
    strncpy_s(new_name, new_len, filename, base_len);
    new_name[base_len] = '\0';
    sprintf(new_name + base_len, ".%s", new_suffix);

    return new_name;
}

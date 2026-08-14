// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#pragma once

#include <stdarg.h>
#include "evibase.h"

#if defined(__clang__) || defined(__GNUC__)
#define PRINTF_LIKE(fmt_index, va_index) __attribute__((format(printf, fmt_index, va_index)))
#define PRINTF_FMT
#elif defined(_MSC_VER)
// Für MSVC: optional SAL für /analyze
#include <sal.h>
#define PRINTF_LIKE(fmt_index, va_index)
#define PRINTF_FMT _Printf_format_string_
#else
#define PRINTF_LIKE(fmt_index, va_index)
#define PRINTF_FMT
#endif

DLLEXPORT char * malloc_printf(const char * fmt, ...) PRINTF_LIKE(1, 2);
DLLEXPORT char * malloc_vprintf(const char *restrict fmt, va_list ap);

typedef enum
{
    TimeStampTypeFile,
    TimeStampTypeISO8601
} TimeStampType_t;

DLLEXPORT char * malloc_timeStamp(TimeStampType_t timeStampType);
DLLEXPORT char * malloc_replace_suffix(const char *filename, const char *new_suffix);

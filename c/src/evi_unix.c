// SPDX-License-Identifier: MIT
// SPDX-FileCopyrightText: © 2024 HSE AG, <opensource@hseag.com>

#include "evibase.h"
#include "eviconfig.h"
#include "crc-16-ccitt.h"
#include <stdio.h>
#include <string.h>
#include <fcntl.h>
#include <unistd.h>
#include <termios.h>
#include <dirent.h>
#include <sys/socket.h>
#include <netdb.h>

#define MIN(x, y) (((x) < (y)) ? (x) : (y))

int findTtyXXX(const char * name, char * devicePath, int devicePathLength)
{
    int ret = -1;
    DIR *dir;
    struct dirent *entry;

    if (!(dir = opendir(name)))
        return -1;

    while ((entry = readdir(dir)) != NULL && ret != 0)
    {
        if (entry->d_type == DT_DIR || entry->d_type == DT_LNK)
        {
            char path[1024] = {0};
            if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
                continue;
            snprintf(path, sizeof(path), "%s/%s", name, entry->d_name);
            strncpy(devicePath, entry->d_name, devicePathLength);
            ret = 0;
        }
    }
    closedir(dir);
    return ret;
}

int findTty(const char * name, int maxDepth, int currentDepth, char * devicePath, int devicePathLength)
{
    int ret = -1;
    DIR *dir;
    struct dirent *entry;

    if(currentDepth >= maxDepth)
        return -1;

    if (!(dir = opendir(name)))
        return -1;

    while ((entry = readdir(dir)) != NULL && ret != 0)
    {
        if (entry->d_type == DT_DIR || entry->d_type == DT_LNK)
        {
            char path[1024] = {0};
            if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
                continue;
            snprintf(path, sizeof(path), "%s/%s", name, entry->d_name);

            if(strcmp(entry->d_name, "tty") == 0)
            {
                ret = findTtyXXX(path, devicePath, devicePathLength);
                break;
            }

            ret = findTty(path, maxDepth, currentDepth + 1, devicePath, devicePathLength);
        }
    }
    closedir(dir);
    return ret;
}

int getDeviceVidPid(const char *dev_path, uint16_t *vid, uint16_t *pid)
{
    char path[256];
    snprintf(path, sizeof(path), "%s/idVendor", dev_path);

    FILE *f_vid = fopen(path, "r");
    if (!f_vid) {
        return -1;
    }
    fscanf(f_vid, "%4hx", vid);  // Read 4 hex digits for VID
    fclose(f_vid);

    snprintf(path, sizeof(path), "%s/idProduct", dev_path);

    FILE *f_pid = fopen(path, "r");
    if (!f_pid) {
        return -1;
    }
    fscanf(f_pid, "%4hx", pid);  // Read 4 hex digits for PID
    fclose(f_pid);

    return 0;
}

int listDir(const char *name, int maxDepth, int currentDepth, char * devicePath, int devicePathLength)
{
    int ret = -1;
    DIR *dir;
    struct dirent *entry;

    if(currentDepth >= maxDepth)
        return -1;

    if (!(dir = opendir(name)))
        return -1;

    while ((entry = readdir(dir)) != NULL && ret != 0)
    {
        if (entry->d_type == DT_DIR || entry->d_type == DT_LNK)
        {
            char path[1024] = {0};
            if (strcmp(entry->d_name, ".") == 0 || strcmp(entry->d_name, "..") == 0)
                continue;

            snprintf(path, sizeof(path), "%s/%s", name, entry->d_name);

            uint16_t devVid;
            uint16_t devPid;
            if(getDeviceVidPid(path, &devVid, &devPid) == 0)
            {
                if(devVid == EVI_COMMON_VID && devPid == EVI_COMMON_PID)
                {
                    ret = findTty(name, 4, 0, devicePath, devicePathLength);
                    if(ret == 0)
                    {
                        break;
                    }
                }
            }

            ret = listDir(path, maxDepth, currentDepth + 1, devicePath, devicePathLength);
        }
    }
    closedir(dir);
    return ret;
}


Error_t eviFindDevice(char *portName, size_t *portNameSize, bool verbose)
{
    char path[64] = {0};
    int found = listDir("/sys/bus/usb/devices", 4, 0, path, sizeof(path));
    
    if(found == 0)
    {
        *portNameSize = snprintf(portName, *portNameSize, "/dev/%s", path);
        return ERROR_EVI_OK;
    }
    else
    {
        return ERROR_EVI_INSTRUMENT_NOT_FOUND;
    }
}

int eviPortOpen(char *portName)
{
    int hComm;
    {
        if(strcmp(portName, "SIMULATION") == 0)
        {
            struct sockaddr_in servaddr;

            // socket create and varification
            hComm = socket(AF_INET, SOCK_STREAM, 0);
            if (hComm == -1)
            {
                fprintf(stderr, "Could not open socket %s\n", portName);
                return -1;
            }

            bzero(&servaddr, sizeof(servaddr));
            servaddr.sin_family = AF_INET;
            servaddr.sin_addr.s_addr = htonl(INADDR_LOOPBACK);
            servaddr.sin_port = htons(5000);

            if (connect(hComm, (struct sockaddr*)&servaddr, sizeof(servaddr)) != 0)
            {
                printf("connection with the server failed...\n");
                exit(0);
            }
            return hComm;
        }
        else
        {
            hComm = open(portName, O_RDWR | O_NOCTTY);
        }
    }

    if (hComm == -1)
    {
        fprintf(stderr, "Could not open port %s\n", portName);
        return -1;
    }

    if (tcflush(hComm, TCIOFLUSH) == -1)
    {
        fprintf(stderr, "Could not flush buffers\n");
        close(hComm);
        return -1;
    }

    // Configure read and write operations to time out after 100 ms.
    struct termios options;
    tcgetattr(hComm, &options);
    options.c_cc[VMIN] = 0;
    options.c_cc[VTIME] = 1;

    if (tcsetattr(hComm, TCSANOW, &options) == -1)
    {
        fprintf(stderr, "Could not set timeouts\n");
        close(hComm);
        return -1;
    }

    // Set the baud rate and other options.
    cfsetispeed(&options, B115200);
    cfsetospeed(&options, B115200);
    options.c_cflag |= (CLOCAL | CREAD);
    options.c_cflag &= ~PARENB;
    options.c_cflag &= ~CSTOPB;
    options.c_cflag &= ~CSIZE;
    options.c_cflag |= CS8;

    if (tcsetattr(hComm, TCSANOW, &options) == -1)
    {
        fprintf(stderr, "Could not set serial settings\n");
        close(hComm);
        return -1;
    }

    return hComm;
}

void eviPortClose(int hComm)
{
    if (hComm != -1)
    {
        close(hComm);
    }
}

bool eviPortWrite(int hComm, char *buffer, bool verbose)
{
    ssize_t written;
    size_t size = strlen(buffer);

    if (verbose)
    {
        fprintf(stderr, "TX: %s\n", buffer);
    }

    written = write(hComm, buffer, size);

    if (written == -1)
    {
        fprintf(stderr, "Could not write to port\n");
        return false;
    }

    if ((size_t)written != size)
    {
        fprintf(stderr, "Could not write all bytes to port\n");
        return false;
    }

    return true;
}

uint32_t eviPortRead(int hComm, char *buffer, size_t size, bool verbose)
{
    ssize_t received;
    size_t count = 0;
    char rx[EVI_MAX_LINE_LENGTH];
    bool waitForStart = true;
    bool done = false;
    bool useChecksum = false;
    int checkSumSeparator = -1;

    do
    {
        memset(rx, 0, EVI_MAX_LINE_LENGTH);
        received = read(hComm, rx, EVI_MAX_LINE_LENGTH);
        if (received == -1)
        {
            fprintf(stderr, "Could not read from port\n");
            return 0;
        }

        if (verbose && received > 0)
        {
            fprintf(stderr, "RX: %s\n", rx);
        }

        for (size_t i = 0; i < (size_t)received && !done; i++)
        {
            if (waitForStart)
            {
                if (rx[i] == EVI_START_NO_CHK || rx[i] == EVI_START_WITH_CHK)
                {
                    waitForStart = false;
                    if (rx[i] == EVI_START_WITH_CHK)
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
                    if (buffer[count] == EVI_CHECKSUM_SEPARATOR)
                    {
                        checkSumSeparator = count;
                    }
                    count++;
                }
            }
        }
    } while (!done);

    if (useChecksum)
    {
        crc_t crcReceived;
        crc_t crc = crc_init();
        crc = crc_update(crc, buffer, checkSumSeparator);
        crc = crc_finalize(crc);
        crcReceived = atoi(buffer + checkSumSeparator + 1);
        if (crc == crcReceived)
        {
            buffer[checkSumSeparator] = 0;
        }
        else
        {
            fprintf(stderr, "CRC differ: received message %s, calculated crc=%i", buffer, (uint32_t)crcReceived);
            return 0;
        }
    }

    return count;
}

errno_t strncat_s(char *restrict dest, rsize_t destsz, const char *restrict src, rsize_t count)
{
    // If s2 < n, we are going to read strlen(s2) + its terminating null byte
    // Otherwise, we are going to read exactly n bytes

    strncat(dest, src, count);
    // should not be necessary
    dest[destsz - 1] = '\0';

    return 0;
}

errno_t strncpy_s(char *restrict dest, rsize_t destsz, const char *restrict src, rsize_t count)
{
    rsize_t m;

    m = MIN(count, destsz - 1);
    strncpy(dest, src, m);
    dest[MIN(count, destsz - 1)] = '\0';

    // on success
    return 0;
}

errno_t strcpy_s(char *restrict dest, rsize_t destsz, const char *restrict src)
{
    strncpy(dest, src, destsz - 1);
    dest[destsz - 1] = '\0';

    // on success
    return 0;
}

int fprintf_s(FILE *stream, const char *format, ...)
{
    va_list args;
    va_start(args, format);

    return vfprintf(stream, format, args);
}

int sprintf_s(char *str, size_t snprintf, const char *format, ...)
{
    va_list args;
    va_start(args, format);

    return vsnprintf(str, snprintf, format, args);
}

void Sleep(uint32_t dwMilliseconds)
{
    sleep(dwMilliseconds);
}

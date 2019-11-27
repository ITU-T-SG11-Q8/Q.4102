#pragma once

void* cpymem(void* dst, const void* src, unsigned int size);
int strlen_s(const char* s);
#ifndef WIN32
int sprintf_s(char *buf, const char *fmt, ...);
int sprintf_s(char *buf, unsigned int size, const char *fmt, ...);
int sscanf_s(const char *str, const char *format, ...);
#endif


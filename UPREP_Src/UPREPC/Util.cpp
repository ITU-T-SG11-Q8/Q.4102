#include "Util.h"
#include <string.h>
#include <stdio.h>
#include <stdarg.h>

void* cpymem(void* dst, const void* src, unsigned int size)
{
	return memmove(dst, src, size);
}

int strlen_s(const char* s)
{
	char* p = (char*)s;
	
	while (*s++);
	
	return s - p - 1;
}

#ifndef WIN32

#define isdigit(c) ((unsigned) ((c) - '0') < 10U)
int sscanf_s(const char *str, const char *format, ...)
{
	const char *start = str;
	va_list args;

	va_start(args, format);
	for ( ; *format != '\0'; format++) {
		if (*format == '%' && format[1] == 'd') {
			int positive;
			int value;
			int *valp;

			if (*str == '-') {
				positive = 0;
				str++;
			} else
				positive = 1;
			if (!isdigit(*str))
				break;
			value = 0;
			do {
				value = (value * 10) - (*str - '0');
				str++;
			} while (isdigit(*str));
			if (positive)
				value = -value;
			valp = va_arg(args, int *);
			*valp = value;
			format++;
		}
		else if (*format == *str) {
			str++;
		}
		else
			break;
	}
	va_end(args);
	return str - start;
}

int sprintf_s(char *buf, const char *fmt, ...)
{
	int n;
	va_list ap;

	va_start(ap, fmt);
	n = vsprintf(buf, fmt, ap);
	va_end(ap);
	return (n);
}

int sprintf_s(char *buf, unsigned int size, const char *fmt, ...)
{
	int n;
	va_list ap;

	va_start(ap, fmt);
	n = vsprintf(buf, fmt, ap);
	va_end(ap);
	return (n);
}
#endif
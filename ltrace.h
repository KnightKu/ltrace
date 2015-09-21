#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>

static int mTraceFD = -1;
int getTraceFD()
{
    if(-1 == mTraceFD)
    {
        mTraceFD = open("/sys/kernel/debug/tracing/trace_marker", O_WRONLY);
    }
    return mTraceFD;
}

#if 0
#define LTRACE_BEGIN(name) \
	do { \
			char buf[1024]; \
			size_t len = snprintf(buf, 1024, "B|%d|%s", getpid(), name); \
			write(getTraceFD(), buf, len); \
		} while(0)

#define LTRACE_END() \
	do { \
			char buf = 'E'; \
			write(getTraceFD(), &buf, 1); \
		} while(0)
#else
#define LTRACE_BEGIN(name)
#define LTRACE_END()
#endif

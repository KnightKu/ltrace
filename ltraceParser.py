#! /usr/bin/python

# @author	jianhui.j.dai@intel.com
# @brief    android system and gfx memory profiler
# @version	0.1
# @date		2015/01/23

import os
import sys
import getopt
import re
import time
from datetime import datetime
import operator
import subprocess
import signal
import csv

g_quit = False

g_procrank_raw_file = 'procrank.txt'
g_geminfo_raw_file = 'gfx_memtrack/i915_gem_meminfo'
g_procmem_sf_raw_file = 'procmem_sf.txt'
g_procmem_media_raw_file = 'procmem_media.txt'

g_adb_shell = None
g_cp = None


def handler(signum, frame):
    global g_quit

    g_quit = True


def preexec_function():
    signal.signal(signal.SIGTERM, signal.SIG_IGN)
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def doParse(out):
    debug_enabled = False

    PROCRANK = out + '/' + g_procrank_raw_file
    procrankFile = file(PROCRANK, 'r')

    SF_PROCMEM = out + '/' + g_procmem_sf_raw_file
    sfProcmemFile = file(SF_PROCMEM, 'r')

    MEDIA_PROCMEM = out + '/' + g_procmem_media_raw_file
    mediaProcmemFile = file(MEDIA_PROCMEM, 'r')

    output_file = out + '/' + 'summary.csv'

    patterns = []

    patterns += [{
        'key': 'TOTAL',
        'item': '0',
        'file': procrankFile,

        'format': ['PSS', None, None, 'VALUE', None, None]
    }]

    patterns += [{
        'key': 'com.android',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'com.android', None, None, 'VALUE', None]
    }]

    patterns += [{
        'key': 'com.android\..*',
        'item': '3',
        'file': procrankFile,

        'format': [None, None, 'NAME', None, None, 'VALUE']
    }]

    patterns += [{
        'key': 'com.google',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'com.google', None, None, 'VALUE', None]
    }]

    patterns += [{
        'key': 'com.google\..*',
        'item': '3',
        'file': procrankFile,

        'format': [None, None, 'NAME', None, None, 'VALUE']
    }]

    patterns += [{
        'key': 'com.intel',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'com.intel', None, None, 'VALUE', None]
    }]
    patterns += [{
        'key': 'com.intel\..*',
        'item': '3',
        'file': procrankFile,

        'format': [None, None, 'NAME', None, None, 'VALUE']
    }]

    patterns += [{
        'key': 'zygote$',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'zygote', None, None, 'VALUE', None]
    }]
    patterns += [{
        'key': 'system_server$',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'system_server', None, None, 'VALUE', None]
    }]
    patterns += [{
        'key': 'coreu$',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'coreu', None, None, 'VALUE', None]
    }]
    patterns += [{
        'key': 'drmserver$',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'drmserver', None, None, 'VALUE', None]
    }]
    patterns += [{
        'key': 'mediaserver$',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'mediaserver', None, None, 'VALUE', None]
    }]

    patterns += [{
        'key': 'heap|malloc]$',
        'item': '2',
        'file': mediaProcmemFile,

        'format': [None, None, 'heap', None, None, 'VALUE']
    }]
    patterns += [{
        'key': '\/drm',
        'item': '2',
        'file': mediaProcmemFile,

        'format': [None, None, 'gem_mapped', None, None, 'VALUE']
    }]
    patterns += [{
        'key': '\.so$',
        'item': '2',
        'file': mediaProcmemFile,

        'format': [None, None, 'libs', None, None, 'VALUE']
    }]

    patterns += [{
        'key': 'surfaceflinger$',
        'item': '3',
        'file': procrankFile,

        'format': [None, 'surfaceflinger', None, None, 'VALUE', None]
    }]

    patterns += [{
        'key': 'heap|malloc]$',
        'item': '2',
        'file': sfProcmemFile,

        'format': [None, None, 'heap', None, None, 'VALUE']
    }]
    patterns += [{
        'key': '\/drm',
        'item': '2',
        'file': sfProcmemFile,

        'format': [None, None, 'gem_mapped', None, None, 'VALUE']
    }]
    patterns += [{
        'key': '\.so$',
        'item': '2',
        'file': sfProcmemFile,

        'format': [None, None, 'libs', None, None, 'VALUE']
    }]

    patterns += [{
        'key': 'RAM:',
        'item': '5',
        'file': procrankFile,

        'format': ['k-buffers', None, None, 'VALUE', None, None]
    }]
    patterns += [{
        'key': 'RAM:',
        'item': '11',
        'file': procrankFile,

        'format': ['k-slab', None, None, 'VALUE', None, None]
    }]

    patterns += [{
        'key': 'RAM:',
        'item': '9',
        'file': procrankFile,

        'format': ['k-gem', None, None, 'VALUE', None, None]
    }]

    for i, p in enumerate(patterns):
        if re.search('\*', p['key']):
            patterns.remove(p)

            foundPattern = 0

            fileObj = p['file']

            fileObj.seek(0, 0)
            for line in fileObj:
                line = line.strip()

                if re.search(p['key'], line):
                    items = line.split()
                    name = items[5]

                    newP = {}
                    newP['key'] = name + '$'
                    newP['item'] = p['item']
                    newP['file'] = p['file']

                    newP['format'] = [None, None, None, None, None, None]

                    index = p['format'].index('NAME')
                    newP['format'][index] = name

                    index = p['format'].index('VALUE')
                    newP['format'][index] = 'VALUE'

                    # print newP['format']
                    patterns.insert(i + foundPattern, newP)
                    foundPattern += 1

    total = 0
    for p in patterns:
        result = 0

        fileObj = p['file']
        fileObj.seek(0, 0)
        for line in fileObj:
            line = line.strip()

            if re.search(p['key'], line):
                items = line.split()
                value = items[int(p['item'])]

                result += int(value.rstrip('kK'))

        index = p['format'].index('VALUE')

        p['format'][index] = "%.2f" % (float(result) / 1024)

        if index == 3:
            total += result

    # add total
    patterns[0:0] = [{
        'key': None,
        'item': None,
        'name': None,
        'file': None,

        'format': ['Total', None, None, "%.2fMB" % (float(total) / 1024), None, None]
    }]

    # write output
    fp = file(output_file, 'wb')
    writer = csv.writer(fp)

    for p in patterns:
        if debug_enabled:
            print p['format']

        writer.writerow(p['format'])

    fp_geminfo = file(out + '/' + g_geminfo_raw_file, 'r')
    started = False
    for line in fp_geminfo:
        if not started:
            if re.search('SharedPHYprop.*PrivPHYsize', line):
                started = True
            continue

        if re.search('-' * 5, line):
            continue

        item = line.split()

        if len(item) > 3 and item[0].isdigit():
            SharedPHYprop = int(item[7].strip('K'))
            PrivPHYsize = int(item[8].strip('K'))
            Gem_all = SharedPHYprop + PrivPHYsize

            writer.writerow(
                [None, item[-1], None, None, "%.2f" % (float(Gem_all) / 1024), None])
            writer.writerow(
                [None, None, 'PrivPHYsize', None, None, "%.2f" % (float(PrivPHYsize) / 1024)])
            writer.writerow(
                [None, None, 'SharedPHYprop', None, None, "%.2f" % (float(SharedPHYprop) / 1024)])

    fp.close()
    fp_geminfo.close()

    return


def captureGemInfo(timestamp, out):
    cmd = g_cp + '/sys/class/drm/card0/gfx_memtrack ' + out + '/gfx_memtrack'

    stream = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, preexec_fn=preexec_function).stdout

    lines = stream.readlines()


def captureProcrank(timestamp, out):
    cmd = g_adb_shell + 'procrank > ' + out + '/' + g_procrank_raw_file

    stream = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=preexec_function).stdout

    # adb shell procrank
    lines = stream.readlines()


def captureProcmem(timestamp, out):
    cmd = g_adb_shell + "ps"

    stream = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=preexec_function).stdout

    mediaserver_pid = 0
    surfaceflinger_pid = 0

    for line in stream.readlines():
        if re.search('surfaceflinger', line):
            surfaceflinger_pid = line.split()[1]

        if re.search('mediaserver', line):
            mediaserver_pid = line.split()[1]

    cmd = g_adb_shell + 'procmem ' + mediaserver_pid + \
        ' > ' + out + '/' + g_procmem_media_raw_file

    stream = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=preexec_function).stdout
    lines = stream.readlines()

    cmd = g_adb_shell + 'procmem ' + surfaceflinger_pid + \
        ' > ' + out + '/' + g_procmem_sf_raw_file

    stream = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=preexec_function).stdout
    lines = stream.readlines()


def captureDumpsys(timestamp, out):
    cmd = g_adb_shell + 'dumpsys > ' + out + '/' + 'dumpsys.txt'
    stream = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=preexec_function).stdout
    lines = stream.readlines()

    cmd = g_adb_shell + 'dmesg > ' + out + '/' + 'dmesg.txt'
    stream = subprocess.Popen(
        cmd, shell=True, stdout=subprocess.PIPE, preexec_fn=preexec_function).stdout
    lines = stream.readlines()

def doMemCapture(loop, interval, out):
    for i in range(loop):
        global g_quit
        if g_quit:
            break

        begin_timestamp = datetime.now()
        '''
        print 'Capture', begin_timestamp
        '''

        # geminfo
        captureGemInfo(begin_timestamp, out)

        '''
        end_timestamp = datetime.now()
        diff_time = end_timestamp - begin_timestamp
        diff_ms = diff_time.seconds * 1000 + diff_time.microseconds / 1000

        print 'Geminfo', diff_ms
        '''
        # done geminfo

        # procrank
        captureProcrank(begin_timestamp, out)

        '''
        end_timestamp = datetime.now()
        diff_time = end_timestamp - begin_timestamp
        diff_ms = diff_time.seconds * 1000 + diff_time.microseconds / 1000

        print 'Procrank', diff_ms
        '''
        # done procrank

        # procmem
        captureProcmem(begin_timestamp, out)

        '''
        end_timestamp = datetime.now()
        diff_time = end_timestamp - begin_timestamp
        diff_ms = diff_time.seconds * 1000 + diff_time.microseconds / 1000

        print 'Procmem', diff_ms
        '''
        # done procmem

        # dumpsys
        captureDumpsys(begin_timestamp, out)
        # done dumpsys

        # delay
        end_timestamp = datetime.now()
        diff_time = end_timestamp - begin_timestamp
        diff_ms = diff_time.seconds * 1000 + diff_time.microseconds / 1000
        # print 'Diff ms', diff_ms

        delay = interval - diff_ms
        if delay > 3:
            # print 'Sleep ', delay
            time.sleep(float(delay) / 1000)

        # parse
        doParse(out)

    return


def PrintUsage():
    print ""
    print "  Usage: " + sys.argv[0]
    print "      -h"
    print "          help"
    print "      -o"
    print "          output directory, default is result"
    print "      -r"
    print "          repeat times, default is 1 time"
    print "      -i"
    print "          interval between each repeat, default is 2s"
    print "      -d"
    print "          delay time before capture, default is 5s"
    print "      -t"
    print "          running on target device, default is host"
    print ""
    print "  Sample: "
    print ""
    print "          " + sys.argv[0]
    print ""
    print "          " + sys.argv[0] + ' -r 2 -o playback'
    print ""
    print "          " + sys.argv[0] + ' -i 3 -r 2 -d 10 -o record'
    print ""
    sys.exit(1)


if __name__ == '__main__':
    try:
        options, arguments = getopt.getopt(sys.argv[1:], "ho:r:i:d:t", [])
    except getopt.GetoptError, error:
        PrintUsage()

    p_out = 'result'
    p_repeat = 1
    p_interval = 2
    p_delay = 1
    p_target = False
    for option, value in options:
        if option == "-h":
            PrintUsage()
        elif option == "-o":
            p_out = value
        elif option == "-r":
            if not value.isdigit():
                PrintUsage()

            p_repeat = int(value)
        elif option == "-i":
            if not value.isdigit():
                PrintUsage()

            if int(value) < p_interval:
                print 'Error:', 'Minimum interval is,', p_interval
                sys.exit(1)

            p_interval = int(value)
        elif option == "-d":
            if not value.isdigit():
                PrintUsage()

            p_delay = int(value)
        elif option == "-t":
            p_target = True
        else:
            PrintUsage()

    print arguments 

    traceFile = file(arguments[0])

    for line in traceFile:
        #print line

        m = re.match(".*\s+(?P<timestamp>\d+\.\d+):\s+sched_switch:\s+prev_comm=(?P<prev_comm>\S+)\s+prev_pid=(?P<prev_pid>\d+).*\s+next_comm=(?P<next_comm>\S+)\s+next_pid=(?P<next_pid>\d+).*", line)
        if m:
            print m.group('timestamp'), m.group('prev_comm'), m.group('prev_pid'), m.group('next_comm'), m.group('next_pid')

    print '*' * 10
    print 'Done'
    print ''

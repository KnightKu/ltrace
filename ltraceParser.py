#! /usr/bin/python

# @author	jianhui.j.dai@intel.com
# @brief        parse ftrace
# @version	0.1
# @date		2015/06/08

import os
import sys
import getopt
import re
import time
import operator
import csv


def timestamp2ms(timestamp):
    tmp = timestamp.split('.')

    return (int(tmp[0]) * 1000000 + int(tmp[1]))


def PrintUsage():
    print ""
    print "  Usage: " + sys.argv[0]
    print "      -h"
    print "          help"
    print "      -o"
    print "          output, default is result.csv"
    print "      -f"
    print "          force overwrite output"
    print ""
    print "  Sample: "
    print ""
    print "          " + sys.argv[0] + ' test.html'
    print ""
    print "          " + sys.argv[0] + ' test.html -o test.csv'
    print ""
    sys.exit(1)


def main():
    try:
        options, arguments = getopt.getopt(sys.argv[1:], "ho:f", [])
    except getopt.GetoptError, error:
        PrintUsage()

    p_output = 'result.csv'
    p_input = None
    p_force_write = False
    for option, value in options:
        if option == "-h":
            PrintUsage()
        elif option == "-o":
            p_output = value
        if option == "-f":
            p_force_write = True
        else:
            PrintUsage()

    if len(arguments) != 1:
        PrintUsage()

    p_input = arguments[0]
    if not os.path.isfile(p_input):
        print '*' * 10
        print 'Error:', 'Input file not existed,', p_input
        print '*' * 10
        PrintUsage()

    if (not p_force_write) and os.path.isfile(p_output):
        print '*' * 10
        print 'Error:', 'Output file existed,', p_output
        print '*' * 10
        PrintUsage()

    traceFile = file(p_input)

    sched_lists = []

    for line in traceFile:
        m = re.match(
            ".*\s+\[(?P<cpu>\d+)\].*\s+(?P<timestamp>\d+\.\d+):\s+sched_switch:\s+prev_comm=(?P<prev_comm>\S+)\s+prev_pid=(?P<prev_pid>\d+).*\s+next_comm=(?P<next_comm>\S+)\s+next_pid=(?P<next_pid>\d+).*", line)

        if m:
            # print m.groups

            sched = {}

            sched['cpu'] = m.group('cpu')
            sched['timestamp'] = m.group('timestamp')
            sched['prev_comm'] = m.group('prev_comm')
            sched['prev_pid'] = m.group('prev_pid')
            sched['next_comm'] = m.group('next_comm')
            sched['next_pid'] = m.group('next_pid')

            sched_lists += [sched]

    traceFile.close()

    if not sched_lists:
        print '*' * 10
        print 'Error:', 'Empty trace'
        print '*' * 10
        sys.exit(1)

    g_duration = timestamp2ms(sched_lists[-1]['timestamp']) - timestamp2ms(
        sched_lists[0]['timestamp'])
    g_duration = float(g_duration / 1000000.0)

    unmatched_sched = []
    thread_sched = []
    core_sched = []

    for sched in sched_lists:
        prev_sched = filter(
            lambda x: x['cpu'] == sched['cpu'], unmatched_sched)

        if len(prev_sched) > 1:
            print 'error!'
            sys.exit(1)

        if prev_sched:
            prev_sched = prev_sched[0]

            if sched['prev_pid'] == prev_sched['next_pid']:

                thread = filter(
                    lambda x: x['pid'] == sched['prev_pid'], thread_sched)
                if thread:
                    thread = thread[0]

                    thread['residency'] += timestamp2ms(
                        sched['timestamp']) - timestamp2ms(prev_sched['timestamp'])
                    thread['wakeup'] += 1
                else:

                    thread = {}

                    thread['pid'] = sched['prev_pid']
                    thread['name'] = sched['prev_comm']
                    thread['residency'] = timestamp2ms(
                        sched['timestamp']) - timestamp2ms(prev_sched['timestamp'])
                    thread['wakeup'] = 1

                    thread_sched += [thread]

                if thread['pid'] != '0':

                    core = filter(
                        lambda x: x['cpu'] == sched['cpu'], core_sched)
                    if core:
                        core = core[0]

                        core['execution time'] += timestamp2ms(
                            sched['timestamp']) - timestamp2ms(prev_sched['timestamp'])

                        core['wakeup'] += 1
                    else:
                        core = {}

                        core['cpu'] = sched['cpu']
                        core['execution time'] = timestamp2ms(
                            sched['timestamp']) - timestamp2ms(prev_sched['timestamp'])

                        core['wakeup'] = 1

                        core_sched += [core]
            else:
                print 'error!'
                sys.exit(1)

            unmatched_sched.remove(prev_sched)

        unmatched_sched += [sched]

    core_sched.sort(key=operator.itemgetter('cpu'))

    allCore = {}
    allCore['cpu'] = 'All'
    allCore['execution time'] = 0
    allCore['wakeup'] = 0

    for core in core_sched:
        allCore['execution time'] += core['execution time']
        allCore['wakeup'] += core['wakeup']

    core_sched += [allCore]

    thread_sched.sort(key=operator.itemgetter(
        'residency', 'pid', 'name', 'wakeup'), reverse=True)

    output = file(p_output, 'w')
    writer = csv.writer(output)

    # title
    writer.writerow(['Trace Time: ' + "%.2fs" % g_duration])

    # core
    writer.writerow(['-' * 50])
    writer.writerow(['Core Residency/Wakeups Info:'])
    writer.writerow(['-' * 50])
    writer.writerow([
        'Core',
        'Execution Times(ms)',
        'Wakeups',
        'Residency'
    ])
    writer.writerow(['-' * 50])
    for core in core_sched:
        writer.writerow([
            core['cpu'],
            "%.3f" % float(core['execution time'] / 1000.0),
            "%.2f/s" % float(core['wakeup'] / g_duration),
            "%.2f" % float(
                core['execution time'] / g_duration / 10000.0) + '%',
        ])

    # thread
    writer.writerow([])
    writer.writerow(['-' * 50])
    writer.writerow(['Process/Thread Residency/Wakups Info:'])
    writer.writerow(['-' * 50])
    writer.writerow([
        'Pid',
        'Thread',
        'Execution Times (ms)',
        'Residency (%)',
        'Wakeup Times',
        'Wakeup (/s)'
    ])
    writer.writerow(['-' * 50])
    for thread in thread_sched:
        # skip idle thread
        if thread['pid'] == '0':
            continue

        writer.writerow([
            thread['pid'],
            thread['name'],
            "%.3f" % float(thread['residency'] / 1000.0),
            "%.2f" % float(thread['residency'] / g_duration / 10000.0) + '%',
            "%.2f" % float(thread['wakeup']),
            "%.2f" % float(thread['wakeup'] / g_duration) + '/s',
        ])
    output.close()

    print '*' * 10
    print 'Done: ', p_output
    print '*' * 10


if __name__ == '__main__':
    main()

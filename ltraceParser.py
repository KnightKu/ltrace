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


def getProcessName(sched_lists, pid):
    name = 'n\\a'

    event = next(
        (x for x in sched_lists if (x['prev_pid'] == pid or x['next_pid'] == pid)), None)

    if event:
        name = event['prev_comm'] if (
            pid == event['prev_pid']) else event['next_comm']
    else:
        # print('pid(' + str(pid) + ') name not found')
        pass

    if pid == 0:
        name = name.split('/')[0]

    return name


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

    g_tgid_supported = False

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
            ".*\s+(?P<tgid>\(.+\)|)\s+\[(?P<cpu>\d+)\].*\s+(?P<timestamp>\d+\.\d+):\s+sched_switch:\s+prev_comm=(?P<prev_comm>.+)\s+prev_pid=(?P<prev_pid>\d+).*\s+next_comm=(?P<next_comm>.+)\s+next_pid=(?P<next_pid>\d+).*", line)

        if m:
            # print m.groups()

            tgid = m.group('tgid')
            if tgid:
                try:
                    tgid = int(tgid.strip('( )'))
                except:
                    tgid = 0

            sched = {}

            sched['tgid'] = tgid
            sched['cpu'] = m.group('cpu')
            sched['timestamp'] = m.group('timestamp')
            sched['prev_comm'] = m.group('prev_comm')
            sched['prev_pid'] = int(m.group('prev_pid'))
            sched['next_comm'] = m.group('next_comm')
            sched['next_pid'] = int(m.group('next_pid'))

            # print sched

            sched_lists += [sched]
        else:
            if re.search('sched_switch:', line):
                raise Exception(
                    'Fatal error, event not matched!' + '\n' + line)

    traceFile.close()

    if not sched_lists:
        raise Exception('Error: empty trace')

    if sched_lists[0]['tgid']:
        g_tgid_supported = True

    g_duration = timestamp2ms(sched_lists[-1]['timestamp']) - timestamp2ms(
        sched_lists[0]['timestamp'])
    g_duration = float(g_duration / 1000000.0)

    unmatched_sched = []
    core_sched = []
    task_sched = []
    thread_sched = []

    # thread and core info
    for sched in sched_lists:

        prev_sched = next(
            (x for x in unmatched_sched if (x['cpu'] == sched['cpu'])), None)

        if prev_sched:

            if sched['prev_pid'] == prev_sched['next_pid']:

                thread = next(
                    (x for x in thread_sched if (x['pid'] == sched['prev_pid'])), None)

                if thread:

                    thread['execution time'] += timestamp2ms(
                        sched['timestamp']) - timestamp2ms(prev_sched['timestamp'])
                    thread['wakeups'] += 1
                else:

                    thread = {}

                    thread['tgid'] = sched['tgid']
                    thread['pid'] = sched['prev_pid']
                    thread['threadName'] = sched['prev_comm']
                    thread['execution time'] = timestamp2ms(
                        sched['timestamp']) - timestamp2ms(prev_sched['timestamp'])
                    thread['wakeups'] = 1

                    thread_sched += [thread]

                if thread['pid'] != 0:

                    core = next(
                        (x for x in core_sched if (x['cpu'] == sched['cpu'])), None)

                    if core:

                        core['execution time'] += timestamp2ms(
                            sched['timestamp']) - timestamp2ms(prev_sched['timestamp'])

                        core['wakeups'] += 1
                    else:
                        core = {}

                        core['cpu'] = sched['cpu']
                        core['execution time'] = timestamp2ms(
                            sched['timestamp']) - timestamp2ms(prev_sched['timestamp'])

                        core['wakeups'] = 1

                        core_sched += [core]
            else:
                raise Exception(
                    'Fatal error, pid not match' + '\n' + prev_sched + '\n' + sched)

            unmatched_sched.remove(prev_sched)

        unmatched_sched += [sched]

    # thread and core info
    core_sched.sort(key=operator.itemgetter('cpu'))

    allCore = {}
    allCore['cpu'] = 'All'
    allCore['execution time'] = 0
    allCore['wakeups'] = 0

    for core in core_sched:
        allCore['execution time'] += core['execution time']
        allCore['wakeups'] += core['wakeups']

    core_sched += [allCore]

    '''
    thread_sched.sort(key=operator.itemgetter(
        'tgid', 'execution time', 'wakeups', 'pid', 'threadName'), reverse=True)
    '''

    # task info
    for thread in thread_sched:
        if thread['pid'] == 0:
            continue

        task = next(
            (x for x in task_sched if (x['tgid'] == thread['tgid'])), None)

        if not task:
            task = {}

            task['tgid'] = thread['tgid']
            task['execution time'] = 0
            task['wakeups'] = 0

            task['threads'] = []

            task_sched += [task]

        task['execution time'] += thread['execution time']
        task['wakeups'] += thread['wakeups']

        threadInTask = next(
            (x for x in task['threads'] if (x['pid'] == thread['pid'])), None)

        if not threadInTask:
            threadInTask = {}

            threadInTask['pid'] = thread['pid']
            threadInTask['threadName'] = thread['threadName']
            threadInTask['execution time'] = thread['execution time']
            threadInTask['wakeups'] = thread['wakeups']

            task['threads'] += [threadInTask]
        else:
            raise 'what is up!'

    task_sched.sort(key=operator.itemgetter(
        'execution time', 'wakeups'), reverse=True)
    for task in task_sched:
        task['threads'].sort(key=operator.itemgetter(
            'execution time', 'wakeups'), reverse=True)

    output = file(p_output, 'w')
    writer = csv.writer(output)

    # write title
    writer.writerow(['-' * 50])
    writer.writerow(['Trace Time: ' + "%.2fs" % g_duration])
    writer.writerow(['-' * 50])

    # write core
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
            "%.2f/s" % float(core['wakeups'] / g_duration),
            "%.2f" % float(
                core['execution time'] / g_duration / 10000.0) + '%',
        ])

    # write task
    writer.writerow([])
    writer.writerow(['-' * 50])
    writer.writerow(['Process/Thread Residency/Wakups Info:'])
    writer.writerow(['-' * 50])

    if g_tgid_supported:

        writer.writerow([
            'Tgid',
            'Process',
            'Pid',
            'Thread',
            'Execution Times (ms)',
            'Residency (%)',
            'Wakeup Times',
            'Wakeup (/s)'
        ])

    else:

        writer.writerow([
            'Pid',
            'Thread',
            'Execution Times (ms)',
            'Residency (%)',
            'Wakeup Times',
            'Wakeup (/s)'
        ])

    writer.writerow(['-' * 50])

    for task in task_sched:
        if g_tgid_supported:

            writer.writerow([])

            writer.writerow([
                task['tgid'],
                getProcessName(sched_lists, task['tgid']),
                None,
                None,
                "%.3f" % float(task['execution time'] / 1000.0),
                "%.2f" % float(
                    task[
                        'execution time'] / g_duration / 10000.0) + '%',
                "%.2f" % float(task['wakeups']),
                "%.2f" % float(
                    task['wakeups'] / g_duration) + '/s',
            ])

            writer.writerow([])

        for threadInTask in task['threads']:
            if g_tgid_supported:

                writer.writerow([
                    None,
                    None,
                    threadInTask['pid'],
                    threadInTask['threadName'],
                    "%.3f" % float(threadInTask['execution time'] / 1000.0),
                    "%.2f" % float(
                        threadInTask[
                            'execution time'] / g_duration / 10000.0) + '%',
                    "%.2f" % float(threadInTask['wakeups']),
                    "%.2f" % float(
                        threadInTask['wakeups'] / g_duration) + '/s',
                ])

            else:

                writer.writerow([
                    threadInTask['pid'],
                    threadInTask['threadName'],
                    "%.3f" % float(threadInTask['execution time'] / 1000.0),
                    "%.2f" % float(
                        threadInTask[
                            'execution time'] / g_duration / 10000.0) + '%',
                    "%.2f" % float(threadInTask['wakeups']),
                    "%.2f" % float(
                        threadInTask['wakeups'] / g_duration) + '/s',
                ])

    # write thread
    '''
    writer.writerow([])
    writer.writerow(['-' * 50])
    writer.writerow(['Process/Thread Residency/Wakups Info:'])
    writer.writerow(['-' * 50])
    writer.writerow([
        'Tgid',
        'Process',
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
        if thread['pid'] == 0:
            continue

        writer.writerow([
            thread['tgid'],
            getProcessName(sched_lists, thread['tgid']),
            thread['pid'],
            thread['threadName'],
            "%.3f" % float(thread['residency'] / 1000.0),
            "%.2f" % float(thread['residency'] / g_duration / 10000.0) + '%',
            "%.2f" % float(thread['wakeups']),
            "%.2f" % float(thread['wakeups'] / g_duration) + '/s',
        ])
    '''

    output.close()

    print '*' * 10
    print 'Done: ', p_output
    print '*' * 10


if __name__ == '__main__':
    main()

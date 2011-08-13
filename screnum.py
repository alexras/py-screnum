#!/usr/bin/env python

import subprocess
import tempfile
import os, sys
import re
import time

def checked_call(cmd, expected_status=0):
    proc_obj = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    output = proc_obj.communicate()[0]

    if proc_obj.returncode != expected_status:
        sys.exit("Command '%s' failed: %s" % (cmd, output))

    return output

def set_window_number(session_name, old_window_number, new_window_number):
    checked_call("screen -S %s -p %d -X number %d" %
                 (session_name, old_window_number, new_window_number))

def get_windows(session_name):
    (tmp_fp, tmpfile) = tempfile.mkstemp()
    os.close(tmp_fp)

    # Create a new session
    screen_session_proc = subprocess.Popen(
        "screen -D -m -S screnum", shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)

    time.sleep(1)

    # Create a new window in this session
    checked_call("screen -S screnum -p 0 -X height 60")

    # Stuff the window list from the primary session into this window
    checked_call('screen -S screnum -p 0 -X stuff '
                 '"screen -x %s -p = \n"' % (session_name))

    time.sleep(1)
    # Dump the window list to the temp file
    checked_call("screen -S screnum -p 0 -X hardcopy %s" % (tmpfile))

    # Get rid of the temporary session
    checked_call("screen -S screnum -p 0 -X kill")
    screen_session_proc.communicate()

    window_extractor_regex = re.compile('^(\d+)\s+(.*?)\s+[^\s]+$')

    windows = {}

    with open(tmpfile, 'r') as fp:
        for line in fp:
            line = line.strip()
            if len(line) > 0:
                match = window_extractor_regex.search(line)
                if match is not None:
                    windows[int(match.group(1))] = match.group(2)

    os.unlink(tmpfile)
    return windows

parent_pid = os.getppid()
if parent_pid == None:
    sys.exit("Can't get parent PID")

parent_screen_pid = int(checked_call(
    "ps -p %s -o ppid --noheaders" % (parent_pid)).strip())

session_re = re.compile("^\s+%d\.(.*?)\s" % (parent_screen_pid))

screen_list = checked_call("screen -ls", expected_status=1).split('\n')

session_name = None

for line in screen_list:
    match = session_re.search(line)
    if match is not None:
        session_name = match.group(1)
        break

if session_name == None:
    sys.exit("Can't get session name")

window_list = get_windows(session_name)

# If I swap with an existing window, our numbers will swap. If I move into a
# new position, my number will change but all other numbers will be unaffected.

window_numbers = sorted(window_list.keys())
num_windows = len(window_numbers)

# Continually place windows from the end of the window list into gaps in the
# front. Not the most efficient implementation in the world from Python's
# perspective, but it fills in the gaps well enough.
for i in xrange(num_windows):
    if i not in window_list:
        max_window_number = window_numbers[-1]
        print "Moving window %d to position %d" % (max_window_number, i)
        time.sleep(1)
        set_window_number(session_name, max_window_number, i)
        window_list[i] = window_list[max_window_number]
        del window_list[max_window_number]
        window_numbers.pop()
        window_numbers.append(i)
        window_numbers.sort()

#!/usr/bin/env python

import subprocess
import tempfile
import os, sys
import re
import time

GNU_SCREEN_MAX_WINDOWS = 40

def checked_call(cmd, expected_status=0):
    """
    Execute the given command in a subprocess shell, and abort if the error
    code isn't what you expected.

    I would use check_output here, but I wanted to make the script compatible
    with Python 2.6.
    """
    proc_obj = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT)
    output = proc_obj.communicate()[0]

    if proc_obj.returncode != expected_status:
        sys.exit("Command '%s' failed: %s" % (cmd, output))

    return output

def set_window_number(session_name, old_window_number, new_window_number):
    """
    Moves the given window number in the given session from old_window_number
    to new_window_number
    """
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

    # Give screen some time to breathe
    time.sleep(1)

    # Create a new window in this session
    checked_call("screen -S screnum -p 0 -X height 60")

    # Stuff the window list from the primary session into this window
    checked_call('screen -S screnum -p 0 -X stuff '
                 '"screen -x %s -p = \n"' % (session_name))

    # Give screen some time to breathe again
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

def screnum():
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
        sys.exit("Can't get session name - keep in mind that you must run "
                 "this from within the screen session you wish to renumber")

    print "Reading window list ..."
    window_list = get_windows(session_name)

    # Convert window mapping into a list giving the window name for each
    # possible window, if any

    windows = [None for i in xrange(GNU_SCREEN_MAX_WINDOWS)]

    for window_number in window_list:
        windows[window_number] = window_list[window_number]

    def swap(i, j):
        """
        Swap the positions of two windows with numbers i and j
        """
        set_window_number(session_name, i, j)

        tmp = windows[i]
        windows[i] = windows[j]
        windows[j] = tmp

        for index in [i,j]:
            if windows[index] == None:
                del window_list[index]
            else:
                window_list[index] = windows[index]

    def min_window(start_index):
        """
        Find the window in the subset of windows whose numbers are >=
        start_index with the smallest name (sorted lexicographically)
        """
        min_window_index = None

        for i in xrange(start_index, GNU_SCREEN_MAX_WINDOWS):
            if windows[i] == None:
                continue

            if min_window_index == None or (
                windows[i] < windows[min_window_index]):

                min_window_index = i

        return min_window_index

    # Perform insertion sort on the windows. Since for whatever reason you
    # can't issue screen commands more than once per second and make them
    # stick, we want to minimize the number of swaps we have to do, at the
    # expense of (negligible) additional CPU time in the script

    for i in xrange(GNU_SCREEN_MAX_WINDOWS):
        smallest_window_number = min_window(i)

        if smallest_window_number == None:
            break
        elif smallest_window_number == i:
            continue
        else:
            time.sleep(1)
            print "Swapping windows %d and %d" % (i, smallest_window_number)
            swap(smallest_window_number, i)

if __name__ == "__main__":
    screnum()

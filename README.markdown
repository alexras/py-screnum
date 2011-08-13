py-screnum
==========

py-screnum is a port of the [screnum](https://launchpad.net/screnum) Bash
script for renumbering windows in [GNU Screen](http://www.gnu.org/s/screen/)
sessions. Its goal is to remove any gaps in window numbering that inevitably
show up when you're opening and closing a lot of windows in a `screen`
session. It also sorts the windows by name.

The previous Bash screnum implementation that implements sorting is inefficient
- it re-reads the window list each time it swaps a window, because it can't
keep sufficient state about the window configuration to remember which windows
were swapped.  It's a lot easier to keep such state around in Python. Also, the
old screnum would swap windows in an infinite loop if two windows had the same
name; my implementation doesn't have that problem, and it was faster to
re-implement the script in Python than to debug the existing Bash script.

As it stands the script is a little slow because there seems to be a limit of
one modification per second for `screen` sessions. I've been careful to
minimize the number of `screen` commands needed to sort the session's windows.

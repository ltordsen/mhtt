""""
General common utilities.
"""
import re
import time as time_module

def nsecs(hhmmss_str):
    """calculate number of seconds.  the string should be formatted as h:mm:ss"""

    if hhmmss_str == 'N/A':
        return hhmmss_str
    tlist = hhmmss_str.split(':')
    hh, mm, ss = int(tlist[0]), int(tlist[1]), int(tlist[2])
    secs = ss + 60*mm + 60*60*hh
    return secs

def secs2text(seconds):
    """Format a time string into seconds"""

    time_fmt = time_module.gmtime(seconds)
    return time_module.strftime("%-H:%M:%S", time_fmt)

def fmt_time_from_txt(time_str):
    """Format a time string into h:mm:s"""

    sec_re = re.compile(r'(\d{1,2})s')
    mmss_re = re.compile(r'(\d{1,2}:\d{1,2})')
    hhmmss_re = re.compile(r'(\d{1,2}:\d{1,2}:\d{1,2})')

    # Format time into hh:mm:ss
    sec_match = re.search(sec_re, time_str)
    hhmmss_match = re.search(hhmmss_re, time_str)
    mmss_match = re.search(mmss_re, time_str)

    formatted_time_str = 'N/A'
    if sec_match:
        secs = sec_match.group(1)
        formatted_time_str = "0:00:%s" % secs
    elif hhmmss_match:
        formatted_time_str = hhmmss_match.group(1)
    elif mmss_match:
        mmss = mmss_match.group(1)
        formatted_time_str = "0:%s" % mmss

    return formatted_time_str

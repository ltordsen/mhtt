#!/usr/bin/env python

import argparse
import copy
import csv
import os
import re
import sys
import time

from pprint import pprint

def get_club_people(club_file_path):
    """ Read a simple textfile of names of club members.  Return a list"""
    if not os.path.exists(club_file_path):
        print "Couldn't find %s" % club_file_path
        sys.exit(1)

    with open(club_file_path, 'r') as fh:
        peeps = fh.read().splitlines()

    return peeps
##########################
# Per Aaron -- time regular expressions
# """
# Match something like 1:09:
# Find: ([0-9]{1}):([0-9]{2})
# Replace with: 00:0$1:$2

# Match something like 10:52:
# Find: ([0-9]{2}):([0-9]{2})
# Replace with: 00:$1:$2
def get_segment_results(args):
    """Read a csv (specified in args) of segment results, and format it."""
    segment_results = dict()
    club_people = get_club_people(args.club)
    all_people = set()

    # I don't think we need to worry about an 'hh:mm:ss' re.  That would
    # be the ideal format anyway.
    sec_re = re.compile(r'(\d{1,2})s')
    mmss_re = re.compile(r'(\d{1,2}:\d{1,2})')
    for csv_path in args.segment_csv:
        if not os.path.exists(csv_path):
            print "Couldn't find %s" % csv_path
            sys.exit(1)

        segname = os.path.basename(csv_path).replace('.csv', '')
        delimiter = args.delimiter if args.delimiter else ','
        print "(get_segment_results)delimiter = \"%s\"" % delimiter

        with open(csv_path) as csvh:
            contents = csv.reader(csvh, delimiter=delimiter)

            for row in contents:
                try:
                    rank, name, date, speed, hr, power, time = \
                    row[0], row[1], row[2], row[3], row[4], row[5], row[6]

                except IndexError:
                    # Shouldn't hit this unless the strava format changes or
                    # there was a copy/paste error when making the csv.
                    print "WARNING: couldn't process row=%s" % row
                    continue
                if rank == 'Rank':
                    # Skip the first/header row.
                    continue
                elif name not in club_people:
                    print "Skipping %s -- not in club" % name
                    continue

                # Format time into hh:mm:ss
                sec_match = re.search(sec_re, time)
                mmss_match= re.search(mmss_re, time)
                if sec_match:
                    secs = sec_match.group(1)
                    #print "sec match:%s" % secs
                    time = "00:00:%s" % secs
                if mmss_match:
                    mmss = mmss_match.group(1)
                    #print "mmss match:%s" % mmss
                    time = "00:%s" % mmss

                if segname in segment_results:
                    segment_results[segname][name] = {
                        'rank': rank, 'date': date,
                        'hr': hr, 'power': power,
                        'time': time, 'speed': speed
                    }
                else:
                     segment_results[segname] = {name: {
                        'rank': rank, 'date': date,
                        'hr': hr, 'power': power,
                        'time': time, 'speed': speed
                    }}
                all_people.add(name)

    print "all_people="
    pprint(all_people)
    pprint(segment_results)

    return segment_results, all_people

def nsecs(hhmmss_str):
    """calculate number of seconds.  the string should be formatted as hh:mm:ss"""

    if hhmmss_str == 'N/A':
        return hhmmss_str
    tlist = hhmmss_str.split(':')
    hh, mm, ss = int(tlist[0]), int(tlist[1]), int(tlist[2])
    secs = ss + 60*mm + 60*60*hh
    return secs

def format_secs(seconds):
    time_fmt = time.gmtime(seconds)
    return time.strftime("%H:%M:%S", time_fmt)

def add_times(sr, all_people):
    # This is probably dependent on what format the input time is in.  I'll
    person_results = dict()

    # Need to account for people missing a segment.  There might be a better
    # way to do this.
    sr_tmp = dict()
    for seg in sr: #sr.keys():
        ranks = [int(sr[seg][p]['rank']) for p in sr[seg].keys()]
        maxrank = max(ranks) + 1 # Incase someone missed a segment
        pprint(ranks)
        for p in all_people:
            if p not in sr[seg].keys():
                print "%s is not in segment %s" % (p, seg)
                if seg not in sr_tmp:
                    sr_tmp[seg] = dict()
                sr_tmp[seg][p] = {'rank': str(maxrank), 'date': 'N/A', 'hr': 'N/A',
                               'power':'N/A', 'time':'N/A', 'speed': 'N/A'}

    # Now copy sr_tmp into sr.
    for seg in sr_tmp:
        for person in sr_tmp[seg]:
            sr[seg][person] = copy.deepcopy(sr_tmp[seg][person])


    print "after appeding sr, sr=\n----"
    pprint(sr)
    print "----"

    for person in all_people:
        total_time = 0
        nsegs = float(len(sr.keys()))
        rank_avg = 0.0
        person_results[person] = dict()
        for seg in sr:
            print "seg=%s" % seg
            ranks = [int(sr[seg][p]['rank']) for p in sr[seg].keys()]
            time = sr[seg][person]['time'];
            if sr[seg][person]['time'] != 'N/A':
                total_time += nsecs(time)
            rank_avg += float(sr[seg][person]['rank'])/nsegs
            print "person=%s, time=%s, total_time=%d, rank=%s, nsegs=%d, rank_avg=%f" % (person, time, total_time, sr[seg][person]['rank'], nsegs, rank_avg)
            person_results[person][seg] = {'time':time, 'time_secs': nsecs(time), 'rank': sr[seg][p]['rank']}

        strtime = format_secs(total_time)
        person_results[person]['total_time'] = strtime
        person_results[person]['rank_avg'] = rank_avg

    return person_results


def main():
    parser = argparse.ArgumentParser('Calculate results')
    parser.add_argument("club", help="a text file with a list of group members")
    parser.add_argument('segment_csv', nargs='+')
    parser.add_argument('-d', '--delimiter', action="store")
    parser.add_argument('-s', '--score', action="store_true")
    #parser.add_argument('-c', '--club', action='store')
    args = parser.parse_args()
    sr,people = get_segment_results(args)
    person_results = add_times(sr, people)

    print "person_results=\n----"
    pprint(person_results)
    print "----"
    if args.score:
        line = "Name#%s#Total Time#Rank Avg" % '#'.join(sr.keys())
    else:
        line = "Name#%s#TotalTime" % '#'.join(sr.keys())
    print line
    for pr in person_results:
        line = "%s#%s#%s" % (pr,
                            '#'.join([person_results[pr][s]['time'] for s in sr.keys()]),
                            person_results[pr]['total_time'])
        if args.score:
            line = "%s#%02f" % (line, person_results[pr]['rank_avg'])
        print line

if __name__ == "__main__":
    main()

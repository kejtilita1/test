#!/usr/bin/env python

# ============================================================================
#
# INTEL CONFIDENTIAL
#
# Copyright 2014-2016 Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its
# suppliers or licensors. Title to the Material remains with Intel
# Corporation or its suppliers and licensors. The Material contains trade
# secrets and proprietary and confidential information of Intel or its
# suppliers and licensors. The Material is protected by worldwide copyright
# and trade secret laws and treaty provisions. No part of the Material may be
# used, copied, reproduced, modified, published, uploaded, posted,
# transmitted, distributed, or disclosed in any way without Intel's prior
# express written permission.
# 
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or
# delivery of the Materials, either expressly, by implication, inducement,
# estoppel or otherwise. Any license under such intellectual property rights
# must be express and approved by Intel in writing.
#
# ============================================================================

"""
Intel site support module. Used supply correct paths to various locations, tools, servers, etc.

Intelsite encapsulates all the site specific locations and settings. Over the years, it has evolved to encapsulate
pretty much everything... It's now a bit of a mush pot of all sorts of things. If you're adding to this module please
only add functions/properties that are site specific.
"""

import sys

sys.dont_write_byte_code = True

import os
import re
import datetime
import socket
import time





def isleapyear(yr):
    """
    Checks whether the provided year is a leap year.
    If a given year is evenly divisible by 4, it is a leap year.
    But if it's also evenly divisible by 100, it is not a leap year.
    But if it's ALSO evenly divisible by 400, it IS a leap year.

    .. note:: This code will need to be revisited about six millennia from now, but it should be good until then.

    :param int yr: The year to check.
    :return: True if the given year is a leap year; otherwise, False
    :rtype: bool
    """

    # TODO: MOVE all of this crap into a intelDateTime.py module. Does not belong here. JSS

    if yr % 400 == 0: return True
    if yr % 100 == 0: return False
    if yr % 4 == 0: return True
    return False


def workweeks(yr):
    """
    Despite the fact that office site calendar numbers days of the week from 1=Monday to 7=Sunday, WW1 is determined to
    be the week containing the first Saturday of the year.  The lower boundary of return values is thus given by a
    non-leap year in which the 7th of January falls on a Saturday.  In this case, New Years Day is actually day 7 of the
    last work week of the previous year, New Years Eve is WW52.7, leaving 364 days, which divides evenly by 7 into 52,
    and so the fewest weeks a year can have is 52 (March, June, September, and December having 5 weeks, all other months
    having 4). The upper boundary of return values is given by a year in which New Years Day falls on a Saturday.  In
    this case, the only days of WW1 that are not part of the previous year are the 1st and 2nd of January, leaving 363
    days, which divides evenly by 7 into 51 with remainder 6.  New Years Day of the following year falls on a Sunday,
    which means that it is part of the previous year, so adding that to 51r6 gives an even 52 weeks, plus WW1 which
    contains the 1st and 2nd gives 53 weeks, which is the maximum number of work weeks in a year -- the extra week is
    added to January.  A nearly-identical case takes place in a leap year wherein New Years Day falls on a Friday.  The
    case of a leap year where New Years day falls on a Saturday is similar also, except that New Years Day of the
    following year falls on a Monday.

    :param int yr: The year to check.
    :return: The number of work weeks in a year of the Intel calendar.
    """

    # TODO: MOVE all of this crap into a intelDateTime.py module. Does not belong here. JSS

    nyd = datetime.date(yr, 1, 1).weekday()  # Determine the day of the week on which the 1st of January fell this year.
    if nyd == 5: return 53  # If the 1st of January fell on a Saturday, the year has 53 weeks.
    if nyd == 4 and isleapyear(yr): return 53  # Same deal if the 1st of January fell on a Friday in a leap year.
    return 52  # All other years have 52 work weeks.


class inteldatetime(datetime.datetime):
    """
    The datetime package's datetime class, plus the ability to express dates in
    Intel's standard-but-quirky dating system (office sites, not factory/production sites)
    * linux ready *
    """

    # TODO: MOVE all of this crap into a intelDateTime.py module. Does not belong here. JSS

    def __init__(self, *args, **kwargs):
        # Instantiate superclass
        datetime.datetime.__init__(self, *args, **kwargs)

        # Determine the current work week and year
        workWeekYear = self.year  # Copy the year, because the Intel year may not be the same as the Gregorian year.
        if self.month == 1 and self.day == 1 and self.isoweekday() == 7:
            # Special case: when the first of January is on a Sunday, it is day .7 of the last work week of the previous year
            workWeekYear -= 1
            workWeek = workweeks(workWeekYear)
        else:
            julian = int(self.strftime("%j"))
            workWeek = int((julian + 5 + ((datetime.date(self.year, 1, 1).weekday() + 1) % 7)) / 7)
            if workWeek > workweeks(workWeekYear): workWeek -= 52; workWeekYear += 1

        # some interesting edge cases
        # Gregorian       Intel
        # Sun 31 Dec 2006 2006WW52.7
        # Mon 01 Jan 2007 2007WW01.1
        # Mon 31 Dec 2007 2008WW01.1
        # Tue 01 Jan 2008 2008WW01.2
        # Wed 02 Jan 2008 2008WW01.3
        # Thu 01 Jan 2009 2009WW01.4
        # Fri 30 Dec 2011 2011WW53.5
        # Sat 31 Dec 2011 2011WW53.6
        # Sun 01 Jan 2012 2011WW53.7
        # Mon 02 Jan 2012 2012WW01.1
        # Tue 03 Jan 2012 2012WW01.2

        # Stuff state variables
        self.workweek = workWeek
        self.workweekyear = workWeekYear
        self.weekday = self.isoweekday()

    def getTimezone(self):
        class IntelTimezone(datetime.tzinfo):
            def __init__(self, timezone_name):
                """
                @param timezone_name:
                """
                self.name = "Unknown"
                self.offset = 0

                if timezone_name in ["Pacific Standard Time",
                                     "America/Los_Angeles",
                                     "America/Vancouver"]:
                    self.name = "PST -8"
                    self.offset = -8

                elif timezone_name in ["Mountain Standard Time",
                                       "America/Denver"]:
                    self.name = "MST -7"
                    self.offset = -7

                elif timezone_name in ["India Standard Time",
                                       "Asia/Kolkata"]:
                    self.name = "IST +5.5"
                    self.offset = 5.5

            def utcoffset(self, dt):
                return datetime.timedelta(hours=self.offset) + self.dst(dt)

            def dst(self, dt):
                # No Daylight Savings Time in Chennai
                if self.name == "IST +5.5":
                    return datetime.timedelta(0)

                # DST starts on second Sunday in March and ends on the first Sunday in November
                first_of_march = datetime.datetime(dt.year, 3, 1)
                first_of_november = datetime.datetime(dt.year, 11, 1)

                second_sunday_in_march = first_of_march + datetime.timedelta(days=7 + 6 - first_of_march.weekday())
                first_sunday_in_november = first_of_november + datetime.timedelta(days=6 - first_of_november.weekday())

                if second_sunday_in_march <= dt.replace(tzinfo=None) < first_sunday_in_november:
                    return datetime.timedelta(hours=1)

                return datetime.timedelta(0)

            def tzname(self, dt):
                return "%s %i" % (self.name, self.offset)

        timezone = IntelTimezone(get_timezone())
        return timezone

    def inteldate(self):
        return (self.workweekyear, self.workweek, self.weekday)

    # TODO: MOVE all of this crap into a intelDateTime.py module. Does not belong here. JSS

    def inteldatetimestring(self):
        """
        YYYYWW##.# HH:MM:SS

        :returns: Datetime as a standardized Intel string
        """
        # TODO: MOVE all of this crap into a intelDateTime.py module. Does not belong here. JSS

        IDT = self.now()
        return "%04dWW%02d.%1d %02d:%02d:%02d" % (
            IDT.workweekyear, IDT.workweek, IDT.weekday, IDT.hour, IDT.minute, IDT.second)


if __name__ == '__main__':
    print "\n --- OS Detection ---"
    print "OS Type: %s" % os.name
    print "OS Version: %s" % getImageRev()

    for s in (None, "LM", "FM", "VC", "CH", "asdf"):
        theSite = Site(override=s)
        print "--- Site Class with Override %s ---" % s
        print "Location:   %s" % theSite.getLocation()
        print "Logs:       %s" % theSite.getLogDir()
        print "Cmd:        %s" % theSite.getCmdDir()
        print "BUST Tests: %s" % theSite.getBUSTTestsDir()
        print "DUT  Tests: %s" % theSite.getDUTTestsDir()
        print "CTF  Tests: %s" % theSite.getCTFTestsDir()
        print "Releases:   %s" % theSite.getReleasesRoot()
        print "Asserts:    %s" % theSite.getAssertDumpsFolder()
        print "Def Maps:   %s" % theSite.getDefectMapDir()
        print "Tools:      %s" % theSite.getToolDir()
        print "TWIDL:      %s" % theSite.getTwidlDir()
        print "SWAT:       %s" % theSite.getSwatReleasesDir()
        print "\n"
        # /for

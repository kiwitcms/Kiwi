# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   Python API for the Kiwi TCMS test case management system.
#   Copyright (c) 2012 Red Hat, Inc. All rights reserved.
#   Author: Petr Splichal <psplicha@redhat.com>
#
#   Copyright (c) 2018 Kiwi TCMS project. All rights reserved.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#   This library is free software; you can redistribute it and/or
#   modify it under the terms of the GNU Lesser General Public
#   License as published by the Free Software Foundation; either
#   version 2.1 of the License, or (at your option) any later version.
#
#   This library is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
#   Lesser General Public License for more details.
#
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

""" Utilities """

import re
import sys

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#  Public Utilities
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


def listed(items, singular=None, plural=None, max=None, quote=""):
    """
    Convert an iterable into a nice, human readable list or description.

    listed(range(1)) .................... 0
    listed(range(2)) .................... 0 and 1
    listed(range(3), quote='"') ......... "0", "1" and "2"
    listed(range(4), max=3) ............. 0, 1, 2 and 1 more
    listed(range(5), 'number', max=3) ... 0, 1, 2 and 2 more numbers
    listed(range(6), 'category') ........ 6 categories
    listed(7, "leaf", "leaves") ......... 7 leaves

    If singular form is provided but max not set the description-only
    mode is activated as shown in the last two examples. Also, an int
    can be used in this case to get a simple inflection functionality.
    """

    # Convert items to list if necessary
    if isinstance(items, int):
        items = range(items)
    elif not isinstance(items, list):
        items = list(items)
    more = " more"
    # Description mode expected when singular provided but no maximum set
    if singular is not None and max is None:
        max = 0
        more = ""
    # Set the default plural form
    if singular is not None and plural is None:
        if singular.endswith("y") and not singular.endswith("ay"):
            plural = singular[:-1] + "ies"
        elif singular.endswith("s"):
            plural = singular + "es"
        else:
            plural = singular + "s"
    # Convert to strings and optionally quote each item
    items = ["{0}{1}{0}".format(quote, item) for item in items]

    # Select the maximum of items and describe the rest if max provided
    if max is not None:
        # Special case when the list is empty (0 items)
        if max == 0 and len(items) == 0:
            return "0 {0}".format(plural)
        # Cut the list if maximum exceeded
        if len(items) > max:
            rest = len(items[max:])
            items = items[:max]
            if singular is not None:
                more += " {0}".format(singular if rest == 1 else plural)
            items.append("{0}{1}".format(rest, more))

    # For two and more items use 'and' instead of the last comma
    if len(items) < 2:
        return "".join(items)
    else:
        return ", ".join(items[0:-2] + [" and ".join(items[-2:])])


def unlisted(text):
    """ Convert human readable list into python list """
    return re.split(r"\s*,\s*|\s+and\s+|\s+", text)


def human(time):
    """ Convert timedelta into a human readable format """
    count = {}
    count["year"] = time.days / 365
    count["month"] = (time.days - 365 * count["year"]) / 30
    count["day"] = 0 if count["year"] > 0 else time.days % 30
    count["hour"] = time.seconds / 3600
    count["minute"] = (time.seconds - 3600 * count["hour"]) / 60
    count["second"] = (
        time.seconds - 3600 * count["hour"] - 60 * count["minute"])
    return listed([
        listed(count[period], period)
        for period in ["year", "month", "day", "hour", "minute", "second"]
        if count[period] > 0 or time.seconds == time.days == 0 and period == "second"])


def info(message, newline=True):
    """ Log provided info message to the standard error output """
    sys.stderr.write(message + ("\n" if newline else ""))


def header(text, width=70):
    """ Print a simple header (text with tilde underline) """
    return "\n{0}\n{1}".format(text, width * "~")

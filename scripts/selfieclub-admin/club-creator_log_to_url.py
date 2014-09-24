#! /usr/bin/env python

import re
import sys

with open(str(sys.argv[1]), 'r') as input:
    for line in input:
        line = line.strip()
        matches = re.search('INFO:root:Created club:  (.*)', line)
        if not matches:
            continue
        data = {}
        exec("data = {}".format(matches.groups()[0]))
        print("http://joinselfie.club/{}/{}".format(data['owner_name'],
                                                    data['club_name']))

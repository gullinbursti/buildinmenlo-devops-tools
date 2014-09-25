#! /usr/bin/env python
# pylint: disable=invalid-name, exec-used

import re
import sys

with open(str(sys.argv[1]), 'r') as input_file:
    for line in input_file:
        line = line.strip()
        matches = re.search('INFO:root:Created club:  (.*)', line)
        if not matches:
            continue
        data = {}
        exec("data = {}".format(matches.groups()[0]))
        print("http://joinselfie.club/{}/{}".format(data['owner_name'],
                                                    data['club_name']))

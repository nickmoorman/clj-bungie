#!/usr/bin/env python

import pprint
import sys
import yaml

if len(sys.argv) == 2:
    # TODO: Verify file exists
    data = yaml.load(file(sys.argv[1], "r"))
else:
    # TODO: Print usage
    print "No file specified!"

uris = []
for endpoint in data:
    uris.append(endpoint["uri"])

pprint.pprint(sorted(uris))

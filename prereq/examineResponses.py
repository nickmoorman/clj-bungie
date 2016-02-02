#!/usr/bin/env python

import collections
import genson
import json
import pprint
import sys
import yaml

# http://stackoverflow.com/a/14692747
def rget(dataDict, mapList):
    return reduce(lambda d, k: d[k], mapList, dataDict)

if len(sys.argv) == 2:
    # TODO: Verify file exists
    data = yaml.load(file(sys.argv[1], "r"))
else:
    # TODO: Print usage
    print "No file specified!"

# Collects unique values for the fields specified in "keys"
def handle(name, data, keys, found, root=[]):
    for key in keys:
        k = root[:]
        k.append(key)
        try:
            val = rget(data, k)
            if key not in found:
                found[key] = collections.Counter()
            if isinstance(val, dict):
                # I don't remember why I commented this out...
                #found[key] = handle(name, val, val.keys(), {})
                found[key].update(val.keys())
            elif isinstance(val, list):
                print name
                found[key].update(["LIST|%s" % name])
            else:
                found[key].update([val])
        except KeyError as ke:
            pass

    return found

# Collects unique values for the fields specified in "keys"
def examine(data, keys, ignore=[], include=None, root=[]):
    print "Examining keys: %s" % keys
    print "Total endpoints: %d" % len(data)
    if include:
        print "Only examining %d endpoint(s)" % len(include)
    else:
        print "Skipping %d endpoint(s); total expected: %d" % (len(ignore), len(data)-len(ignore))

    found = {}
    for endpoint in data:
        name = endpoint["name"]
        if (include and name in include) or (not include and name not in ignore):
            res = json.loads(endpoint["exampleResponses"][0])
            handle(name, res, keys, found, root)

    print "Summary:"
    pprint.pprint(found)

"""
examine(
    data,
    ["ErrorCode", "ThrottleSeconds", "ErrorStatus", "Message", "MessageData"],
    ["GetGrimoireDefinition"]
)

examine(
    data,
    ["Response"],
    ["GetGrimoireDefinition", "EquipItem", "SetItemLockState", "SetQuestTrackedState", "TransferItem", "GetMembershipIdByDisplayName"]
)

examine(
    data,
    ["allPvP", "allStrikes", "patrol", "raid", "story", "focusMembershipId", "focusCharacterId"],
    include=["GetHistoricalStats", "GetLeaderboards", "GetLeaderboardsForPsn", "GetLeaderboardsForCharacter"],
    root=["Response"]
)
"""

# Generates a JSON schema for the responses of the endpoint names passed in
def generateSchema(data, endpoints):
    schema = genson.Schema()
    for endpoint in data:
        if endpoint["name"] in endpoints:
            res = json.loads(endpoint["exampleResponses"][0])
            schema.add_object(res["Response"])

    print json.dumps(schema.to_dict(), sort_keys=True, indent=4, separators=(",", ": "))

generateSchema(data, ["GetDestinyLiveTileContentItems"]) 
#generateSchema(data, ["SearchDestinyPlayer"]) 

"""
generateSchema(
    data,
    ["GetHistoricalStats", "GetLeaderboards", "GetLeaderboardsForPsn", "GetLeaderboardsForCharacter"]
)"""

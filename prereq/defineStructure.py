#!/usr/bin/env python

import collections
import json
import pprint
import sys
import yaml

if len(sys.argv) == 2:
    # TODO: Verify file exists
    data = yaml.load(file(sys.argv[1], "r"))
else:
    # TODO: Print usage
    print "No file specified!"

# Groups of common response elements
groups = [
    ["allPvP", "allStrikes", "patrol", "raid", "story"],
    ["focusMembershipId"]
]

# Endpoints to ignore and why
# NOTE: GetExcellenceBadges contains data and definitions, but definitions should be optional
ignoreWithReasons = {
    "EquipItem": "Response: 0",
    "GetDestinyLiveTileContentItems": "List of single object",
    "GetGrimoireDefinition": "No example response available",
    "GetMembershipIdByDisplayName": "Response: 4611686018428939884 (unicode)",
    "SetQuestTrackedState": "Response: 0",
    "TransferItem": "Response: 0",
    "SearchDestinyPlayer": "List of single object",
    "SetItemLockState": "Response: 0",
    "GetHistoricalStats": "Group 1",
    "GetLeaderboards": "Group 1 & Group 2",
    "GetLeaderboardsForCharacter": "Group 1 & Group 2 + 'focusCharacterId'",
    "GetLeaderboardsForPsn": "Group 1 & Group 2",
    "GetDestinyManifest": "Unique Response",
    "GetHistoricalStatsDefinition": "Unique Response",
    "GetMyGrimoire": "Unique Response",
    "EquipItems": "Unique Response",
    "GetHistoricalStatsForAccount": "Unique Response"
}
ignoreKeys = ignoreWithReasons.keys()
expected = ["Response", "ErrorCode", "ThrottleSeconds", "ErrorStatus", "Message", "MessageData"]
found = {}

# List of endpoint names keyed by response element name
dataToEndpoint = {}
# List of response element names keyed by endpoint name
endpointToData = {}

# Things found under the "Response" element when it's an object
rdata = {}

print "Total endpoints: %d" % len(data)
print "Skipping %d endpoints; total expected: %d" % (len(ignoreKeys), len(data)-len(ignoreKeys))
# This is ugly AF; this experiment led to a much more generic recursive
# approach to response summarization, which can be found in
# generateSchemas.py and examineResponses.py
for endpoint in data:
    if endpoint["name"] not in ignoreKeys:
        if "exampleResponses" in endpoint:
            res = json.loads(endpoint["exampleResponses"][0])
            for f in expected:
                if f in res:
                    if f not in found:
                        found[f] = collections.Counter()
                    if f == "Response":
                        # Most Response elements are objects, so we'll just
                        # summarize the keys found inside
                        keys = res[f].keys()
                        if endpoint["name"] not in endpointToData:
                            endpointToData[endpoint["name"]] = set()
                        for k in keys:
                            if k != "definitions":
                                if k not in dataToEndpoint:
                                    dataToEndpoint[k] = set()
                                dataToEndpoint[k].add(endpoint["name"])
                                if k != "data":
                                    endpointToData[endpoint["name"]].add(k)
                                else:
                                    rdata[endpoint["name"]] = res[f][k]
                        found[f].update(keys)
                    elif f == "MessageData":
                        found[f].update(res[f].keys())
                    else:
                        found[f].update([res[f]])
                else:
                    print "%s not found in %s" % (f, endpoint["name"])
            # Write the example response out to a pretty-printed JSON file so
            # it's easy for us to manually inspect it
            json.dump(res, file("responses/%s.json" % endpoint["name"], "w"), sort_keys=True, indent=4, separators=(",", ": "))
        else:
            print "No example responses for %s" % endpoint["name"]

del dataToEndpoint["data"]
endpointToData = {k:v for (k,v) in endpointToData.items() if len(v) > 0}

print "SUMMARY"
pprint.pprint(found)
print "Data To Endpoint"
pprint.pprint(dataToEndpoint)
print "Endpoint To Data"
pprint.pprint(endpointToData)
#pprint.pprint(filter(lambda x: len(x.value) > 0, endpointToData))

dataKeys = collections.Counter()
for k, v in rdata.items():
    dataKeys.update(v.keys())

pprint.pprint(rdata.keys())
pprint.pprint(dataKeys)

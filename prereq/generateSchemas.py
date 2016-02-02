#!/usr/bin/env python

import collections
import copy
import genson
import json
import pprint
import sys
import yaml

# http://stackoverflow.com/a/14692747
def rget(dataDict, mapList):
    return reduce(lambda d, k: d[k], mapList, dataDict)
def rset(dataDict, mapList, value):
    rget(dataDict, mapList[:-1])[mapList[-1]] = value

if len(sys.argv) == 2:
    # TODO: Verify file exists
    data = yaml.load(file(sys.argv[1], "r"))
else:
    # TODO: Print usage
    print "No file specified!"

# Generates a JSON schema for the "Response" field in a given response object
def generateSchema(res):
    schema = genson.Schema()
    schema.add_object(res["Response"])

    return schema.to_dict()

# Recursively removes all "required" elements from the generated schema;
# "required" is not accurately defined through this automated process (at least
# not yet...)
def removeRequired(schema):
    if schema["type"] == "object":
        if "required" in schema:
            del schema["required"]
        for k, v in schema["properties"].items():
            removeRequired(v)
    elif schema["type"] == "array":
        for s in schema["items"]:
            removeRequired(s)

# Given all endpoint data and a list of endpoint names, generates JSON schemas
# for the relevant example responses
def generate(data, endpoints=None):
    schemas = {}
    for endpoint in data:
        if endpoints == None or endpoint["name"] in endpoints:
            if "exampleResponses" in endpoint:
                schema = generateSchema(json.loads(endpoint["exampleResponses"][0]))
                # Remove "required" fields
                removeRequired(schema)
                schemas[endpoint["name"]] = schema
    
    return schemas

# Allows us to generate a "hash map" of distinct schema objects
# Borrowed from: http://stackoverflow.com/a/8714242
def makeHash(o):
    """
    Makes a hash from a dictionary, list, tuple or set to any level, that contains
    only other hashable types (including any lists, tuples, sets, and
    dictionaries).
    """

    if isinstance(o, (set, tuple, list)):
        return tuple([makeHash(e) for e in o])    
    elif not isinstance(o, dict):
        return hash(o)

    new_o = copy.deepcopy(o)
    for k, v in new_o.items():
        new_o[k] = makeHash(v)

    return hash(tuple(frozenset(sorted(new_o.items()))))

# Recursively generates a literal "hash map" whose entries show the schema
# identified by the hash (the map's key), and all locations where that schema
# can be found.  Example:
# {
#     '549719752616736597': {
#         'paths': [
#             'GetHistoricalStats|allStrikes',
#             'GetHistoricalStats|raid',
#             'GetHistoricalStats|allPvP',
#             'GetHistoricalStats|patrol'
#         ],
#         'schema': {
#             'properties': {
#                 'allTime': {
#                     'properties': {},
#                     'type': 'object'
#                 }
#             },
#             'type': 'object'
#         }
#     }
# }
def buildHashes(path, schema, hashes={}):
    if schema["type"] == "object" and schema["properties"]:
        h = makeHash(schema["properties"])
        if h not in hashes:
            hashes[h] = {
                "schema": schema,
                "paths": []
            }
        hashes[h]["paths"].append(path)
        for k, v in schema["properties"].items():
            buildHashes("%s|%s" % (path, k), v, hashes)
    elif schema["type"] == "array":
        for s in schema["items"]:
            buildHashes("%s|items0" % path, s, hashes)

    return hashes

# Helper that takes a simple path string and returns a list that can be passed
# to rget() to retrieve the schema object it identifies
def pathToSchemaAccessor(path):
    parts = path.split("|")
    l = [parts[0]]
    for p in parts[1:]:
        if p == "items0":
            l.append("items")
            l.append(0)
        else:
            l.append("properties")
            l.append(p)

    return l

# Helper that takes a simple path string and retrieves the schema object it
# identifies
def getSchemaByPath(schemas, path):
    return rget(schemas, pathToSchemaAccessor(path))

# Helper that takes a simple path string and returns a list that can be passed
# to rget() to retrieve the response object it identifies
def pathToObjectAccessor(path):
    parts = path.split("|")
    l = ["Response"]
    for p in parts[1:]:
        if p == "items0":
            l.append(0)
        else:
            l.append(p)

    return l

# Helper that takes a simple path string and retrieves the response object it
# identifies
def getObjectByPath(data, path):
    for endpoint in data:
        if endpoint["name"] == path.split("|", 1)[0]:
            res = json.loads(endpoint["exampleResponses"][0])

            return rget(res, pathToObjectAccessor(path))


# NOTE: From here on, it gets really messy...  The process is almost complete,
# but I'm having trouble getting everything to work properly, hence all the
# commented-out sections of code where I keep trying things in hopes that
# they'll work

# What should happen now:
# 1. Generate schemas for all responses
# 2. Build "hash map" identifying common sub-schemas


"""
schemas = generate(
    data,
    ["GetHistoricalStats", "GetLeaderboards", "GetLeaderboardsForPsn", "GetLeaderboardsForCharacter"]
)
"""
#name = "GetDestinyLiveTileContentItems"
#name = "GetHistoricalStats"
#name = "GetDestinyAccountSummary"
#schemas = generate(data, [name])
#s = schemas[name]
schemas = generate(data)
hashes = {}
for name, schema in schemas.items():
    hashes = buildHashes(name, schema, hashes)

hashes = {k:v for k, v in hashes.items() if len(v["paths"]) > 1}

#print json.dumps(s, sort_keys=True, indent=4, separators=(",", ": "))
#hashes = buildHashes(name, s)
#pprint.pprint(hashes)
print "%d common sub-schemas found" % len(hashes.keys())
#pprint.pprint(hashes[9185188520799617012])
#pprint.pprint(hashes[8075652936413879214]["schema"])
#pprint.pprint(getSchemaByPath(schemas, hashes[8075652936413879214]["paths"][0]))
#pprint.pprint(getObjectByPath(data, hashes[8075652936413879214]["paths"][0]))

#json.dump(schemas, file("schemas-no-refs.json", "w"))

# Map of replacements for each endpoint.  Each entry is itself a map which lists
# the hash of the schema object to reference at the given location.  Example:
# {
#     'GetHistoricalStats': {
#         'GetHistoricalStats|allPvP': 549719752616736597,
#         'GetHistoricalStats|allStrikes': 549719752616736597,
#         'GetHistoricalStats|patrol': 549719752616736597,
#         'GetHistoricalStats|raid': 549719752616736597
#     }
# }
replacements = {}

# Identify sub-schemas that should be replaced with references to a common
# object
for k, v in hashes.items():
    for path in v["paths"]:
        accessor = pathToSchemaAccessor(path)
        if accessor[0] not in replacements:
            replacements[accessor[0]] = {}
            #replacements[accessor[0]] = []
        replacements[accessor[0]][path] = k
        #replacements[accessor[0]].append({
        #    "path": accessor[1:],
        #    "schemaHash": k
        #})
    schemas[k] = v["schema"]

#pprint.pprint(replacements)

# Re-stringifies the exploded-and-processed path
def pathToString(path):
    return "|".join(str(p) for p in path)

# Make all required replacements.  We need to sort the replacements
# alphabetically because if we replace an object, then we've implicitly already
# replaced all of its sub-objects, and we no longer need to process a
# replacement for them
# TODO: This is the part that I can't quite get figured out...  >_<
print "%d schemas requiring replacements" % len(replacements)
for name, schema in schemas.items():
    if name in replacements:
        replacements[name] = collections.OrderedDict(sorted(replacements[name].items(), key=lambda t: t[0]))
        #paths = [pathToString(rep for rep in replacements[name].keys()]
        #for path in paths:
        #    parts = path.split("|")
        #    valid = {}
        #    for p in parts:
        #        if p in valid:
        for path, schemaHash in replacements[name].items():
            visited = []
            #print visited
            #print path
            if len(visited) == 0:
                print path
                rset(schema, pathToSchemaAccessor(path)[1:], { "$ref": "#/%s" % schemaHash })
                visited.append(path)
            else:
                for v in visited:
                    #print "checking"
                    #print v
                    #print path
                    if v in path:
                        #print "breaking"
                        break
                else:
                    #print "hey there"
                    #rset(schema, pathToSchemaAccessor("|".join(path.split("|")[1:])), { "$ref": "#/%s" % schemaHash })
                    visited.append(path)
                    print path
                    rset(schema, pathToSchemaAccessor(path)[1:], { "$ref": "#/%s" % schemaHash })

"""
            else:
                print "nuupe"
                print path
                visited.append(path)
                #rset(schema, pathToSchemaAccessor("|".join(path.split("|")[1:])), { "$ref": "#/%s" % schemaHash })
                rset(schema, pathToSchemaAccessor(path)[1:], { "$ref": "#/%s" % schemaHash })
"""

"""
        validPaths = [paths[0]]
        print name
        for path in paths[1:]:
            print path
            for vp in validPaths:
                #print "Comparing..."
                #print vp
                #print path
                if vp not in path:
                    validPaths.append(path)
                    #print "Breaking"
                    #print validPaths
        #pprint.pprint(validPaths)
        #for rep in replacements[name]:
            #d
            #rset(schema, rep["path"], { "$ref": "#/%s" % rep["schemaHash"] })
"""

#exit()
json.dump(schemas, file("schemas-with-refs.json", "w"))

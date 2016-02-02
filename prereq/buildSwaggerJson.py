#!/usr/bin/env python

import collections
import genson
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

# Top-level object that describes the API using the OpenAPI Specification
# See: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md
swagger = {
    "swagger": "2.0",
    "info": {
        "title": "Bungie API (Destiny endpoints only!)",
        "description": "Bungie's API, only focusing on Destiny-related endpoints for now",
        "version": "1.0.0"
    },
    "host": "www.bungie.net",
    "basePath": "/Platform",
    "schemes": [
        "http",
        "https"
    ],
    "consumes": [
        "application/json"
    ],
    "produces": [
        "application/json"
    ],
    "paths": {},
    # Data types that can be consumed/produced by operations
    "definitions": {},
    # Parameters used across multiple operations
    "parameters": {},
    # Responses reused across operations
    "responses": {},
    "securityDefinitions": {
        "apiKey": {
            "type": "apiKey",
            "name": "X-API-KEY",
            "description": "Bungie API Key",
            "in": "header"
        },
        "csrf": {
            # TODO: See if oauth2 would make more sense here
            "type": "apiKey",
            "name": "X-CSRF",
            "description": "CSRF token, equal to the 'bungled' cookie from bungie.net",
            "in": "header"
        },
        "cookie": {
            # TODO: See if oauth2 would make more sense here
            "type": "apiKey",
            "name": "Cookie",
            "description": "The following cookie values from bungie.net: 'bungled', 'bungledid', 'bungleatk'",
            "in": "header"
        },
    },
    "security": {
        "apiKey": []
    },
    "tags": [
        {
            "name": "all",
            "description": "Convenient listing of all endpoints"
        },
        # Accessibility tags
        {
            "name": "public",
            "description": "General endpoints",
            "externalDocs": {
                "description": "More info",
                "url": "http://bungienetplatform.wikia.com/wiki/Category:PublicEndpoint"
            }
        },
        {
            "name": "private",
            "description": "Endpoints requiring authentication",
            "externalDocs": {
                "description": "More info",
                "url": "http://bungienetplatform.wikia.com/wiki/Category:PrivateEndpoint"
            }
        },
        # Purpose tags
        {
            "name": "p-ungrouped",
            "description": "Ungrouped endpoints"
        },
        {
            "name": "p-account",
            "description": "Relating to a player's account"
        },
        {
            "name": "p-advisors",
            "description": "Advisors about events, special or otherwise"
        },
        {
            "name": "p-character",
            "description": "Relating to a player's characters"
        },
        {
            "name": "p-lookups",
            "description": "Relating to the Grimoire, manifest, etc."
        },
        {
            "name": "p-stats",
            "description": "Relating to stats"
        },
        {
            "name": "p-vendors",
            "description": "Relating to vendors and their inventories"
        }
    ]
}

dummyResponseData = {
    "200": {
        "description": "FILL ME IN"
    }
}

# Definitions of objects used in requests/responses
definitions = {}

# Operation objects keyed by endpoint name
operations = {}

# Tags to apply to each operation, for now just purpose-based tags
tagMap = {
    "EquipItem": ["character", "maybe-items"],
    "EquipItems": ["character", "maybe-items"],
    "GetAccount": ["account"],
    "GetActivityHistory": ["stats"],
    "GetAdvisorsForCharacter": ["unsure-advisors-or-character"],
    "GetAdvisorsForCurrentCharacter": ["unsure-advisors-or-character"],
    "GetCharacter": ["character"],
    "GetCharacterActivities": ["character"],
    "GetCharacterInventory": ["character", "maybe-items"],
    "GetCharacterProgression": ["character"],
    "GetCharacterSummary": ["character"],
    "GetDestinyAccountSummary": ["account"],
    "GetDestinyAggregateActivityStats": ["stats"],
    "GetDestinyExplorerItems": ["lookups"],
    "GetDestinyExplorerTalentNodeSteps": ["lookups"],
    "GetDestinyLiveTileContentItems": ["lookups"],
    "GetDestinyManifest": ["lookups"],
    "GetDestinySingleDefinition": ["lookups"],
    "GetExcellenceBadges": ["stats"],
    "GetGrimoireByMembership": ["unsure-account-or-lookups"],
    "GetGrimoireDefinition": ["lookups"],
    "GetHistoricalStats": ["stats"],
    "GetHistoricalStatsDefinition": ["stats"],
    "GetHistoricalStatsForAccount": ["stats"],
    "GetItemDetail": ["character", "maybe-items"],
    "GetLeaderboards": ["stats"],
    "GetLeaderboardsForCharacter": ["stats"],
    "GetLeaderboardsForPsn": ["stats"],
    "GetMembershipIdByDisplayName": ["account"],
    "GetMyGrimoire": ["unsure-account-or-lookups"],
    "GetPostGameCarnageReport": ["stats"],
    "GetPublicAdvisors": ["advisors"],
    "GetPublicVendor": ["vendors"],
    "GetPublicVendorWithMetadata": ["vendors"],
    "GetPublicXurVendor": ["unsure-advisors-or-vendors"],
    "GetSpecialEventAdvisors": ["advisors"],
    "GetTriumphs": ["account"],
    "GetUniqueWeaponHistory": ["stats"],
    "GetVault": ["account", "maybe-items"],
    "GetVendorForCurrentCharacter": ["unsure-character-or-vendors"],
    "GetVendorForCurrentCharacterWithMetadata": ["unsure-character-or-vendors"],
    "GetVendorItemDetailForCurrentCharacter": ["unsure-character-or-vendors"],
    "GetVendorItemDetailForCurrentCharacterWithMetadata": ["unsure-character-or-vendors"],
    "GetVendorSummariesForCurrentCharacter": ["unsure-character-or-vendors"],
    "SearchDestinyPlayer": ["unsure-account-or-lookups"],
    "SetItemLockState": ["character", "maybe-items"],
    "SetQuestTrackedState": ["character"],
    "TransferItem": ["account", "maybe-items"]
}

# Generates information about an "operation", which is basically a specific
# REST call
def generateOperation(endpoint, tagMap):
    operation = {
        "tags": ["all", endpoint["accessibility"]],
        "summary": endpoint["name"],
        "description": endpoint["description"],
        "externalDocs": {
            "description": "Wikia page",
            "url": "http://bungienetplatform.wikia.com/wiki/" + endpoint["name"]
        },
        "operationId": endpoint["name"],
        "produces": [
            "application/json"
        ]
    }

    # Add tags from the map above
    mappedTags = tagMap[endpoint["name"]]
    if len(mappedTags) > 0:
        operation["tags"].extend("p-%s" % tag for tag in mappedTags)
    else:
        operation["tags"].append("p-ungrouped")

    # Parameters
    # TODO: params for type "header" and "formData"(?)
    params = None
    if "pathVariables" in endpoint or "queryStringVariables" in endpoint or "jsonBodyVariables" in endpoint:
        params = []
    if "pathVariables" in endpoint:
        for varName, varDesc in endpoint["pathVariables"].iteritems():
            # TODO: Properly set "type"
            param = {
                "name": varName,
                "in": "path",
                "description": varDesc,
                "required": True,
                "type": "string"
            }
            params.append(param)
    if "queryStringVariables" in endpoint:
        for varName, varDesc in endpoint["queryStringVariables"].iteritems():
            # TODO: Properly set "type" and "required"
            param = {
                "name": varName,
                "in": "query",
                "description": varDesc,
                "type": "string"
            }
            params.append(param)
    if "jsonBodyVariables" in endpoint:
        operation["consumes"] = ["application/json"]

    # JSON body for POST requests
    if endpoint["httpMethod"] == "post":
        exampleRequest = json.loads(endpoint["exampleRequest"])
        schema = genson.Schema()
        schema.add_object(exampleRequest)
        s = schema.to_dict()
        s["example"] = exampleRequest
        # TODO: Maybe add the schema to the global definitions instead of
        # inlining here?
        params.append({
            "name": "body",
            "in": "body",
            "schema": s
        })

    if params is not None:
        operation["parameters"] = params

    # Responses
    responses = { "200": { "description": "FILL ME IN" } }

    # NOTE: Actually including the schemas here generates an enormous JSON file
    # that causes Swagger to choke when trying to load it; generateSchemas.py
    # will allow us to extract common objects from the set of all responses so
    # we can define them once in the global "definitions" object and simply
    # refer to them wherever they're used in specific responses
    if "exampleResponses" in endpoint:
        #exampleResponse = json.loads(endpoint["exampleResponses"][0])
        schema = genson.Schema()
        #schema.add_object(exampleResponse)
        #responses["200"]["schema"] = schema.to_dict()
        #responses["200"]["examples"] = { "application/json": exampleResponse }

    operation["responses"] = responses

    # Security
    if endpoint["accessibility"] == "private":
        operation["security"] = {
            "apiKey": [],
            "csrf": [],
            "cookie": []
        }

    return operation

# TODO: Generate Swagger files for:
# - all endpoints, no response models or examples
# - each group, including models/examples
# - ???

# Loop over endpoint data from the API docs and munge them into a format that
# Swagger will understand
for endpoint in data:
    path = swagger["paths"][endpoint["uri"]] if endpoint["uri"] in swagger["paths"] else {}
    operation = generateOperation(endpoint, tagMap)
    #operations[endpoint["name"]] = {
    #    "httpMethod": endpoint["httpMethod"],
    #    "uri": endpoint["uri"],
    #    "operation": operation
    #}
    path[endpoint["httpMethod"]] = operation
    swagger["paths"][endpoint["uri"]] = path

#def buildJsonFile(operations, filename, includes):

# Sort everything by URI so things are easy to find while browsing
swagger["paths"] = collections.OrderedDict(sorted(swagger["paths"].items()))

# Write the final JSON file
json.dump(swagger, file("destinyservice.json", "w"))

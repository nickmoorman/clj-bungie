# Pre-Requisites for the API Wrapper

This directory holds a lot of exploratory code that will eventually be used to
create the Clojure wrapper around Bungie's API.  It consists of a set of Python
scripts that were written to gather specific information about various parts of
the API documentation data.

Please note that this code was written as a rapid prototype, and as such most
of it is very hacky or otherwise poorly written.  Portions will be cleaned up
for further use after "exploration" is complete.

## Background

Bungie has some [official documentation][1] available, but it's lacking
information about a lot of the available endpoints.  The community-run
BungieNetPlatform Wikia site provides a much more thorough reference for all
available [endpoints][2].

## The Road to a Wrapper

This is a quick overview of what I want to accomplish before I can start on the
actual wrapper:

1. Scrape the Wikia site to obtain all necessary information about all API
   endpoints (URIs, parameters available, whether authentication is required,
   etc.)
2. Get the data into a form that's more readily accessible than sifting through
   wiki pages
3. Determine a good logical grouping for the endpoints to inform a good layout
   for the wrapper's namespaces
4. Possibly generate a skeleton to start the actual wrapper code

## Getting Started With The Code

I've been working with Python 2.7.10; I make no claims to knowing how well
everything works with any other version.  You'll need to make sure you have the
following Python modules installed:

- PyYaml ([PyPI][3], [docs][4])
- genson ([PyPI][5], [GitHub][6])

You'll also need to check out the [Swagger UI repo][7], as well as the
[WikiScraper][8] script that I wrote for this project (which requires the
[mwparserfromhell library][9], also available through `pip`).

### What's Inside?

The most important files are `destinyservice.yml`, `buildSwaggerJson.py`, and
`generateSchemas.py`.  A quick overview of the rest though:

- `defineStructure.py` - hacked together during initial exploration of the
  example API responses available in the documentation; prints a summary of the
  elements found in each example response, and writes each response out to a
  pretty-printed JSON file
- `examineResponses.py` - builds off of work done in `defineStructure.py` to
  show a more in-depth summary of things found in example responses; also a
  first attempt at generating JSON schemas
- `listUris.py` - dead simple script to list the endpoint URIs in alphabetical
  order

Now, the more important ones.

#### `destinyservice.yml`

This file is the input to `wikiscraper.py`.  It defines the process for
extracting structured data from the BungieNetPlatform wiki.

#### `buildSwaggerJson.py`

This script will take the output from WikiScraper and build a JSON file that
describes the API endpoints collected using the [OpenAPI Spec][10].  This file
can then be fed into Swagger UI for a much more pleasant way to browse the API
docs.  More importantly, I've coded in some "tags" that tell Swagger to group
the endpoints in certain ways.  There's a group for all the endpoints, a group
each for "public" and "private" endpoints ("private" endpoints being those that
require authentication), and then a set of purpose-based groups (account-related
endpoints, character-related endpoints, etc.).  There are also some groups for
endpoint groupings I'm unsure about.

#### `generateSchemas.py`

Work in progress...  The goal of this script is to generate a set of JSON
schemas to describe all API responses as concisely as possible.  If the
responses are fed to Swagger in full, Swagger gets overloaded due to the size of
the data.  To solve this problem, this script is being developed to recursively
generate a JSON schema for every object and sub-object found in each response,
and then replace any common objects with a reference to the single definition of
the respective object.  The script is almost complete; I believe the last piece
is getting it to ignore any sub-objects of an object that's already been
replaced with a reference.  I hammered away at this for too long last week and
haven't gotten a chance to take another look since.

### Putting It All Together...

Now that everything has been more-or-less described, you probably want to know
the answer to "ok, so how the hell do I run this?".  Well, here's how!

The first step for all further work is to run `wikiscraper.py`, passing
`destinyservice.yml` as the singular argument:

    $ ./wikiscraper.py /path/to/clj-bungie/prereq/destinyservice.yml

This will generate two files: `endpoints.yml` and `endpoints-loadable.yml`.
These files will contain the API documentation that's been extracted from the
wiki, broken down into usable key/value pairs.  The files are the same, except
that the first is generated with `yaml.safe_dump()` and the second with
`yaml.dump()`, so the latter can be loaded by other Python scripts.

#### Visualizing the documentation with Swagger

Use the extracted endpoint data to generate the OpenAPI JSON for Swagger:

    $ ./buildSwaggerJson.py endpoints-loadable.yml

This will generate the file `destinyservice.json`.  Swagger UI is just HTML and
Javascript, so it requires no server to run.  However, in order to load our JSON
file, it helps to run a simple HTTP server to run the files.  I like to symlink
the `destinyservice.json` file into swagger-ui's `dist` directory, and then from
there run:

    $ python -m SimpleHTTPServer

Load up Swagger UI at http://localhost:8000/ and then put the URL to the
generated JSON file (http://localhost:8000/destinyservice.json) in at the top
and hit "Explore".  This will allow you to browse the documentation (sans
example responses for now), complete with the ability to see the logical tag
groups that I've come up with so far.

#### Working on concise schema generation

Run the schema generation script:

    $ ./generateSchemas.py endpoints-loadable.yml

It will throw a `KeyError`.  This is because it's trying to replace a schema
whose parent has already been replaced (for example, in the case of
[GetVendorSummariesForCurrentCharacter][11], if a replacement attempt is made
for `ackState` after `vendors` has already been replaced by a reference).  Once
this issue is resolved, I _think_ the schema-condensing algorithm will be
complete, and it can then be integrated with `buildSwaggerJson.py`.

## Next Steps

I've created some [milestones][12] and [issues][13] in GitHub to describe and
prioritize the work required to get this project going.

[1]: https://www.bungie.net/platform/destiny/help/
[2]: http://bungienetplatform.wikia.com/wiki/Category:Endpoint
[3]: https://pypi.python.org/pypi/PyYAML/3.11
[4]: http://pyyaml.org/wiki/PyYAMLDocumentation
[5]: https://pypi.python.org/pypi/genson/0.1.0
[6]: https://github.com/wolverdude/genson
[7]: https://github.com/swagger-api/swagger-ui
[8]: https://github.com/nickmoorman/wikiscraper
[9]: https://github.com/earwig/mwparserfromhell
[10]: https://github.com/OAI/OpenAPI-Specification/blob/master/versions/2.0.md
[11]: http://bungienetplatform.wikia.com/wiki/GetVendorSummariesForCurrentCharacter
[12]: https://github.com/nickmoorman/clj-bungie/milestones
[13]: https://github.com/nickmoorman/clj-bungie/issues

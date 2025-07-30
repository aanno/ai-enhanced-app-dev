# mcp-python TODO backlog

* fix highlighting on client
* `read server-status`: number of tools.total_calls is always 0 (count this value up on calls)
* there is no way to look at "example:greet:args:schema" and "example:greet:result:schema"
  + there should be new shell command for this
  + my proposal: `tool-details <toolname>` should list (among other) arg schema and result schema (highlighted)

## completion (JSON and other)

Some tests on this (non-interactive) would be very helpful!

mcp> 
works (suggests: help, list, tools, ...)

mcp> call 
does not work (suggests: help, list, tool, ... instead of example:greet, example:greetingJson, ...)

mcp> call example:greet
No space at end!
Maybe ok: (suggests: example:greet, example:greetingJson, example:greetingJson:args:schema, example:greetingJson:result:schema)
but the latter 2 (example:greetingJson:args:schema, example:greetingJson:result:schema) are wrong here

mcp> call example:greetingJson (space at end)
works (suggests: '{')

mcp> call example:greetingJson { 
works (suggests: "name", "include_details", "preferences")

mcp> call example:greetingJson { "include_details": true
does not work (suggests: '}' instead of ',' and '}'

mcp> call example:greetingJson { "include_details": true,  "name": "kjsks
Maybe ok: (suggests nothing instead of '"') 

mcp> call example:greetingJson { "include_details": true,  "name": "kjsks", "preferences": { "for  
Maybe ok: (suggests nothing indead of 'mat":')

mcp> call example:greetingJson { "include_details": true,  "name": "kjsks", "preferences": { "format":
does not work (suggests '} }' instead of "detailed", "normal" )

mcp> call example:greetingJson { "include_details": true,  "name": "kjsks", "preferences": { "format": "
does not work (suggests 'name"', 'include_details"', 'preferences"' instead of 'detailed"', 'simple"')

Jinja2.registerTest 'callable', (object) -> 
 !!(obj && obj.constructor && obj.call && obj.apply)

Jinja2.registerTest 'odd', (value) -> value%2==1

Jinja2.registerTest 'even', (value) -> value%2==0

Jinja2.registerTest 'divisibleby', (value, num) -> value%num==0

Jinja2.registerTest 'defined', (value) -> typeof value != "undefined"

Jinja2.registerTest 'undefined', (value) -> typeof value == "undefined"

Jinja2.registerTest 'none', (value) -> value==null

Jinja2.registerTest 'lower', (value) -> value==value.toLowerCase()

Jinja2.registerTest 'upper', (value) -> value==value.toUpperCase()

Jinja2.registerTest 'string', (value) ->
  toString.call(value) == '[object String]'
  
Jinja2.registerTest 'mapping', (value) ->
  value is Object(value)
  
Jinja2.registerTest 'number', (value) ->
  toString.call(value) == '[object Number]'
  
Jinja2.registerTest 'sequence', (value) ->
  toString.call(value) == '[object Array]'

Jinja2.registerTest 'sameas', (value, other) ->
  value is other

Jinja2.registerTest 'iterable', (value) ->
  toString.call(value) == '[object Array]';

Jinja2.registerTest 'escaped', (value) -> 
  '__html__' in value


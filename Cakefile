# Module requires
{spawn, exec} = require 'child_process'
sys = require 'sys'
Closure = require 'closure-compiler'

printOutput = (process) ->
  process.stdout.on 'data', (data) -> sys.print data
  process.stderr.on 'data', (data) -> sys.print data

watchJS = ->
  coffee = exec 'coffee -cj ./jinja2js/lib/runtime.js ./jinja2js/src/runtime.coffee ./jinja2js/src/globals.coffee ./jinja2js/src/filters.coffee ./jinja2js/src/tests.coffee '
  # closure = Closure.compile null, js:'./jinja2js/lib/runtime.js', js_output_file:'./jinja2js/lib/runtime.min.js', ->
  printOutput(coffee)


task 'sbuild', 'Build task for Sublime Text', ->
  watchJS()

# Module requires
{spawn, exec} = require 'child_process'
sys = require 'sys'
Closure = require 'closure-compiler'

printOutput = (process) ->
  process.stdout.on 'data', (data) -> sys.print data
  process.stderr.on 'data', (data) -> sys.print data

watchJS = ->
  coffee = exec 'coffee -cj ./jsjinja/lib/jinja2.runtime.js ./jsjinja/src/runtime.coffee ./jsjinja/src/globals.coffee ./jsjinja/src/filters.coffee ./jsjinja/src/tests.coffee '
  closure = Closure.compile null, js:'./jsjinja/lib/jinja2.runtime.js', js_output_file:'./jsjinja/lib/jinja2.runtime.min.js', ->
  printOutput(coffee)


task 'sbuild', 'Build task for Sublime Text', ->
  watchJS()

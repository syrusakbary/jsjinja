`__hasProp = {}.hasOwnProperty,
__extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };
`
root = exports ? this

new_context = (environment, template_name, blocks, vars, shared, globals, locals) ->
  vars = vars or {}
  parent = (if shared then vars else globals)
  new Context(environment, parent, template_name, blocks)

class Set
  add: (o) ->
    @[o] = true
  remove: (o) ->
    delete @[o]

class Template
  constructor: (@environment) ->
  
  root: ->
  
  render: (obj) ->
    context = new Context(@environment, null, null, @blocks)
    context.vars = obj
    @root context
  
  module: ->
    context = new Context(@environment)
    @root context
    module = {}
    for key in context.exported_vars
      module[key] = context.vars[key]
    module
  
  new_context: (vars, shared, locals) ->
    new_context @environment, @name, @blocks, vars, shared, @globals, locals

class Context
  constructor: (@environment, @parent, name, blocks) ->
      @vars = {}
      @blocks = {}
      for block_name of blocks
        @blocks[block_name] = [blocks[block_name]]
      @exported_vars = new Set()
  super: (name, current) ->
      blocks = @blocks[name]
      index = blocks.indexOf(current) + 1
      blocks[index]

  resolve: (key) ->
      @vars[key] or @parent?.resolve(key)

  call: (f, args, kwargs) ->
      call_args = []
      for arg of f.__args__
        call_args.push kwargs[f.__args__[arg]] or args.pop()
      f.apply null, call_args


Jinja2 =

  templates: {}
  
  filters: {}

  registerFilter: (name, func) ->
    @filters[name] = func

  getFilter: (name) ->
    @filters[name]

  registerTemplate: (name, template) ->
    @templates[name] = template

  getTemplate: (name) ->
    new @templates[name]

  utils:
    to_string: (x) ->
      (if x then String(x) else "")

    missing: `undefined`

    loop: (i, len) ->
      first: i is 0
      last: i is (len - 1)
      index: i + 1
      index0: i
      revindex: len - i
      revindex0: len - i - 1
      length: len

  extends: `__extends`
  Template: Template
  Context: Context

Jinja2.registerFilter 'capitalize', (str) ->
  str.charAt(0).toUpperCase() + str.slice(1)

Jinja2.registerFilter 'escape', (html) ->
  String(html).replace(/&(?!(\w+|\#\d+);)/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace /"/g, "&quot;"

root.Jinja2 = Jinja2
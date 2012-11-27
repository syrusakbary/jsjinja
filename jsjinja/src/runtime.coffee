`__hasProp = {}.hasOwnProperty,
__extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };
`
root = exports ? this

new_context = (template_name, blocks, vars, shared, globals, locals) ->
  vars = vars or {}
  parent = (if shared then vars else globals)
  new Context(parent, template_name, blocks)

class Set
  add: (o) ->
    @[o] = true
  remove: (o) ->
    delete @[o]

class Template
  constructor: ->
    @blocks = {}
    for key of @
      if key.indexOf('block_')==0
        k = key.slice(6)
        @blocks[k] = this[key] 
        @blocks[k].__append_context__ = true

  root: ->
  
  render: (obj) ->
    context = new Context(null, null, @blocks)
    context.vars = obj
    @root context
  
  module: ->
    context = new Context
    @root context
    module = {}
    for key of context.exported_vars
      module[key] = context.vars[key]
    module
  
  new_context: (vars, shared, locals) ->
    new_context @name, @blocks, vars, shared, @globals, locals

class Context
  constructor: (@parent, name, blocks) ->
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
      @vars[key] or @parent?.resolve(key) or Jinja2.globals[key]

  call: (f, args, kwargs) ->
      return if not f
      call_args = if not f.__args__ then args else []
      if f.__append_context__
        call_args.push(@)
      if f.__append_args__
        call_args.push(args)
      if f.__append_kwargs__
        call_args.push(kwargs)

      for arg of f.__args__
        call_args.push kwargs[f.__args__?[arg]] or args.pop()
      f.apply (f.constructor or null), call_args

  callfilter: (f, preargs, args, kwargs) ->
      return if not f
      call_args = preargs
      for arg of f.__args__
        call_args.push kwargs[f.__args__[arg]] or args.pop()
      f.apply null, call_args


Jinja2 =

  templates: {}
  
  filters: {}

  globals: {}

  tests: {}

  registerGlobal: (key, value) ->
    @globals[key] = value

  registerFilter: (name, func) ->
    @filters[name] = func

  registerTest: (name, func) ->
    @tests[name] = func

  getFilter: (name) ->
    @filters[name]

  registerTemplate: (name, template) ->
    @templates[name] = template

  getTemplate: (name, from) ->
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
      cycle: -> arguments[i%arguments.length]
  extends: `__extends`
  Template: Template
  Context: Context

root.Jinja2 = Jinja2
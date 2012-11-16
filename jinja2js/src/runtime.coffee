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
      @blocks[key.slice(6)] = this[key] if key.indexOf('block_')==0

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
      @vars[key] or @parent?.resolve(key)

  call: (f, args, kwargs) ->
      call_args = if not f.__args__ then args else []
      for arg of f.__args__
        call_args.push kwargs[f.__args__?[arg]] or args.pop()
      f.apply null, call_args

  callfilter: (f, preargs, args, kwargs) ->
      call_args = preargs
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

Jinja2.registerFilter 'capitalize', (str) ->
  str.charAt(0).toUpperCase() + str.slice(1)

Jinja2.registerFilter 'escape', (html) ->
  String(html).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace /"/g, "&quot;"

Jinja2.registerFilter 'default', (value, default_value, boolean) ->
  if ((boolean and !value) or (value is undefined)) then default_value else value

Jinja2.registerFilter 'truncate', (str, length, killwords, end) ->
  length or= 255
  end or='...'
  if str.length <= length
    str
  else if killwords
    str.substring(0, length)
  else
    str = str.substring(0, maxLength + 1)
    str = str.substring(0, Math.min(str.length, str.lastIndexOf(" ")))
    str + end

Jinja2.registerFilter 'length', (obj) -> obj.length
Jinja2.registerFilter 'count', (obj) -> obj.length

Jinja2.registerFilter 'indent', (str, width, indentfirst) ->
  width or=4
  indention = if width then Array(width + 1).join(" ") else ""
  (if indentfirst then str else str.replace(/\n$/,'')).replace(/\n/g,"\n#{indention}")

Jinja2.registerFilter 'random', (environment, seq) ->
  if seq then seq[Math.floor(Math.random() * seq.length)] else `undefined`

Jinja2.registerFilter 'last', (environment, seq) ->
  if seq then seq[seq.length-1] else `undefined`

Jinja2.registerFilter 'first', (environment, seq) ->
  if seq then seq[0] else `undefined`

Jinja2.registerFilter 'title', (str) ->
  str.replace /\w\S*/g, (txt) -> txt.charAt(0).toUpperCase() + txt.substr(1).toLowerCase()

Jinja2.registerFilter 'lower', (str) -> str.toLowerCase()

Jinja2.registerFilter 'upper', (str) -> str.toUpperCase()

root.Jinja2 = Jinja2
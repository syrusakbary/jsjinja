`__hasProp = {}.hasOwnProperty,
__extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };
`
root = exports ? this

clone = (obj) ->
  target = {}
  for i of obj
    target[i] = obj[i]  if obj.hasOwnProperty(i)
  target

merge_options = (obj1, obj2) ->
  obj3 = {}
  for attrname of obj1
    obj3[attrname] = obj1[attrname]
  for attrname of obj2
    obj3[attrname] = obj2[attrname]
  obj3

new_context = (template_name, blocks, vars, shared, globals, locals) ->
  vars = vars or {}
  parent = (if shared then vars else merge_options(globals or {}, vars))
  if locals
    if shared
      parent = clone(parent)
    for attrname of locals
      parent[attrname] = locals[attrname] if locals[attrname] isnt Jinja2.utils.missing
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
  
  new_context: (vars, shared, locals) ->
    new_context @name, @blocks, vars, !!shared, @globals, locals

  render: (obj) ->
    @root @new_context(obj)
  
  render_block: (name, obj) ->
    context = new Context(null, null, @blocks)
    context.vars = obj
    @["block_#{name}"] context
  
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
    if @vars?.hasOwnProperty(key)
      return @vars[key]
    if @parent?.resolve
      return @parent.resolve(key)
    if @parent?.hasOwnProperty(key)
      return @parent[key]
    return Jinja2.globals[key]

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

  version: 0.2
  
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

    format: (str,arr) ->
      callback = (exp, p0, p1, p2, p3, p4) ->
        return "%"  if exp is "%%"
        return `undefined`  if arr[++i] is `undefined`
        exp = (if p2 then parseInt(p2.substr(1)) else `undefined`)
        base = (if p3 then parseInt(p3.substr(1)) else `undefined`)
        val = undefined
        switch p4
          when "s"
            val = arr[i]
          when "c"
            val = arr[i][0]
          when "f"
            val = parseFloat(arr[i]).toFixed(exp)
          when "p"
            val = parseFloat(arr[i]).toPrecision(exp)
          when "e"
            val = parseFloat(arr[i]).toExponential(exp)
          when "x"
            val = parseInt(arr[i]).toString((if base then base else 16))
          when "d"
            val = parseFloat(parseInt(arr[i], (if base then base else 10)).toPrecision(exp)).toFixed(0)
        val = (if typeof (val) is "object" then JSON.stringify(val) else val.toString(base))
        sz = parseInt(p1) # padding size
        ch = (if p1 and p1[0] is "0" then "0" else " ") # isnull?
        val = (if p0 isnt `undefined` then val + ch else ch + val)  while val.length < sz # isminus?
        val
      i = -1
      regex = /%(-)?(0?[0-9]+)?([.][0-9]+)?([#][0-9]+)?([scfpexd])/g
      str.replace regex, callback
    
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
Jinja2.registerGlobal 'range', ->
  start = undefined
  end = undefined
  step = undefined
  array = []
  switch arguments.length
    # when 0
    #   throw new Error("range() expected at least 1 argument, got 0 - must be specified as [start,] stop[, step]")return array
    when 1
      start = 0
      end = Math.floor(arguments[0]) - 1
      step = 1
    when 2, 3
    # else
      start = Math.floor(arguments[0])
      end = Math.floor(arguments[1]) - 1
      s = arguments[2]
      s = 1  if typeof s is "undefined"
      step = Math.floor(s) # or (->
      #   throw new Error("range() step argument must not be zero")
      # )()
  if step > 0
    i = start

    while i <= end
      array.push i
      i += step
  else if step < 0
    step = -step
    if start > end
      i = start

      while i > end + 1
        array.push i
        i -= step
  array

Jinja2.registerGlobal 'dict', (->
    func = (obj) ->  obj
    func.__append_kwargs__ = true
    func
  )()

# class Cycler
#   constructor: (items) ->
#     log? '*****', @items
#     @reset()

#   reset: ->
#     @setPos 0

#   setPos: (@pos) ->
#     @current = @items[@pos]

#   next: ->
#     log? '*****___', @pos
#     rv = @current
#     @setPos (@pos+1)% (@items.length)
#     rv

Jinja2.registerGlobal 'cycler', -> 
  # log? arguments[0],arguments[1]
  cycler = 
    items: arguments
    reset: ->
      cycler._setPos 0
    _setPos: (pos) ->
      cycler.pos = pos
      cycler.current = cycler.items[pos]
    next: ->
      rv = cycler.current
      cycler._setPos (cycler.pos+1)%(cycler.items.length)
      rv
  cycler.reset()
  return cycler
  # new Cycler(['odd','even'])

Jinja2.registerGlobal 'joiner', (sep) ->
  sep or= ','
  used = false
  ->
    if not used
      used = true
      ''
    else
      sep
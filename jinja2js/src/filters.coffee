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


Jinja2.registerFilter 'capitalize', (str) ->
  str.charAt(0).toUpperCase() + str.slice(1)

Jinja2.registerFilter 'escape', (html) ->
  String(html).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace /"/g, "&quot;"

Jinja2.registerFilter 'default', (value, default_value, bool) ->
  if ((bool and !value) or (value is undefined)) then default_value else value

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

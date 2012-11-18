Jinja2Js: Render Jinja2 Templates in JS
=======================================

Jinja2Js lets you use your [Jinja2](http://jinja.pocoo.org/) templates
in Javascript. It **compile the Jinja2 templates to Javascript with 
no restrictions**.

The js can be generated via command line `jinja2js <template file>` or through the `{% jinja2js %}` tag in the templates.

You can use:

* Template inheritance (Include, Extends, Blocks, super, ...)
* Import
* Macros
* Tests
* Filters
* Tags

The only exception is that **you cannot use custom tags** like `{% customtag %}{% endcustomtag %}`.


# Nutshell

Here a small example of a Jinja template:

```html
{% extends 'base.html' %}
{% block title %}Memberlist{% endblock %}
{% block content %}
  <ul>
  {% for user in users %}
    <li><a href="{{ user.url }}">{{ user.username }}</a></li>
  {% endfor %}
  </ul>
{% endblock %}
```

And here is the javascript compiled template:

```js
(function() {
    Jinja2.extends(Template, Jinja2.Template);
    Jinja2.registerTemplate("readme_template.tmpl", Template);
    function Template() {return Template.__super__.constructor.apply(this, arguments);};
    Template.prototype.root = function (context) {
        var buf = "";
        var parent_template = Jinja2.getTemplate("base.html", "readme_template.tmpl");
        for (name in parent_template.blocks) {
            var parent_block = parent_template.blocks[name];
            context.blocks[name] = context.blocks[name] || [];
            context.blocks[name].push(parent_block)
        }
        buf += parent_template.root(context);
        return buf;
    }
    Template.prototype.block_content = function (context) {
        var buf = "";
        var l_users = context.resolve("users");
        buf += "\n  <ul>\n  ";
        var l_user = undefined;
        var t_1 = l_users;
        for (var t_2= 0, t_3 = t_1.length; t_2<t_3; t_2++) {
            l_user = t_1[t_2];
            buf += '\n    <li><a href="';
            buf += l_user['url'];
            buf += '">';
            buf += l_user['username'];
            buf += '</a></li>\n  ';
        }
        l_user = undefined;
        buf += "\n  </ul>\n";
        return buf;
    }
    Template.prototype.block_title = function (context) {
        var buf = "";
        buf += "Memberlist";
        return buf;
    }
    return Template;
})()
```

# Installation

For begin using Jinja2Js just add `jinja2js.ext.Jinja2JsExtension` to your Jinja2 Environment.

Example:

```python
import jinja2
env = jinja2.Environment(extensions=['jinja2js.ext.Jinja2JsExtension',])
```

Or:

```python
jinja_env.add_extension('jinja2js.ext.Jinja2JsExtension')
```

# Usage

## Generating js templates

Once you have the Jinja2Js extension installed, you have to generate the js templates:

```python
	print jinja_env.jinja2js.generate('your_template.jinja2')
```

Or just converting all

```python
	print jinja_env.jinja2js.generate_all()
```

Or using the command line script

```
$> jinja2js yourtemplate.jinja2
```


## Rendering the js templates

For start using the templates you must include the `runtime.js` script:

```html
	<script src="https://raw.github.com/SyrusAkbary/jinja2js/master/jinja2js/lib/runtime.min.js">
```

After you have included `runtime.js` and the generated js templates, then

```js
	html = Jinja2.get(""readme_template.tmpl").render({}})
	$('body').html(html)
```

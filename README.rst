JsJinja: Render Jinja2 Templates in JS
======================================

JsJinja lets you use your `Jinja2`_ templates in Javascript. It
**compile the Jinja2 templates to Javascript with no restrictions**.

The js can be generated via command line ``jsjinja <template file>`` or
through the ``{% jsjinja %}`` tag in the templates.

You can use:

-  Template inheritance (Include, Extends, Blocks, super, …)
-  Import
-  Macros
-  Tests
-  Filters
-  Tags

The only exception is that **you cannot use custom tags** like
``{% customtag %}{% endcustomtag %}``.


Installing
----------

First, you must do:

::

    pip install jsjinja


Nutshell
========

Here a small example of a Jinja template:

.. code:: html+django

    {% extends 'base.html' %}
    {% block title %}Memberlist{% endblock %}
    {% block content %}
      <ul>
      {% for user in users %}
        <li><a href="{{ user.url }}">{{ user.username }}</a></li>
      {% endfor %}
      </ul>
    {% endblock %}

And here is the javascript compiled template:

.. code:: javascript

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

Installation
============

For begin using JsJinja just add ``jsjinja.ext.JsJinjaExtension`` to
your Jinja2 Environment.

Example:

.. code:: python

    import jinja2
    env = jinja2.Environment(extensions=['jsjinja.ext.JsJinjaExtension',])

Or:

.. code:: python

    jinja_env.add_extension('jsjinja.ext.JsJinjaExtension')

Usage
=====

Generating js templates
-----------------------

Once you have the JsJinja extension installed, you have to generate the
js templates:

.. code:: python

    print jinja_env.jsjinja.generate('your_template.jinja2')

Or just converting all

.. code:: python

    print jinja_env.jsjinja.generate_all()

Or using the **command line utility**

::

    jsjinja <templates>

Rendering the js templates
--------------------------

For start using the templates you must include the ``jinja2.runtime.js``
script:

.. code:: html

    <script src="https://raw.github.com/SyrusAkbary/jsjinja/master/jsjinja/lib/jinja2.runtime.min.js"></script>

After you have included ``jinja2.runtime.js`` and the generated js
templates, then

.. code:: javascript

    html = Jinja2.getTemplate("template.html").render({}})
    $('body').html(html)

Examples
========

Library comes with a lot of examples, you can find them in `examples`_
directory.

-  `Static`_ generation
-  `Dynamic`_ generation

Testing
=======

You must have ``pyv8`` and ``nose`` python packages installed. You can
do the tests with

::

    ./test.sh

TODOs and BUGS
==============

See: http://github.com/syrusakbary/jsjinja/issues

.. _Jinja2: http://jinja.pocoo.org/
.. _examples: https://github.com/SyrusAkbary/jsjinja/tree/master/examples/
.. _Static: https://github.com/SyrusAkbary/jsjinja/tree/master/examples/static
.. _Dynamic: https://github.com/SyrusAkbary/jsjinja/tree/master/examples/dynamic

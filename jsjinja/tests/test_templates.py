#encoding: utf8
import os
import jinja2
import jsjinja

from nose import with_setup


def setup_func():
    global jinja_env, processors

def teardown_func():
    pass


from pyv8 import PyV8

TEMPLATE_FOLDER = 'templates/'
env = jinja2.Environment(loader = jinja2.FileSystemLoader(TEMPLATE_FOLDER))
env.add_extension('jsjinja.ext.JsJinjaExtension')

class Global(PyV8.JSClass): 
  def log(self,*args):
    print args



ctx = PyV8.JSContext(Global())
ctx.enter()

ctx.eval(jsjinja.lib())


# templates = env.list_templates()

def test_extension():
    js = env.jsjinja.generate_source(source='{{a}}')
    ex = ctx.eval('(new (%s))'%js).render({"a":"test"})
    assert ex == "test"

def test_extensiontag():
    template = '''{% jsjinja %}{% macro x(s) %}{{s}}{% endmacro %}{% endjsjinja %}'''
    t = env.from_string(template)
    js = str(t.render())
    print js
    ex = ctx.eval('(new (%s))'%js).module().x("test")
    assert ex == "test"

code = env.jsjinja.generate_all()
# raise Exception(code) 
ctx.eval(code)

context = {'context':True}


def compare_templates(f):
    jinja_template = env.get_template(f).render(context)
    # raise Exception(ctx.locals.Jinja2.templates[f])
    js_template = ctx.locals.Jinja2.getTemplate(f)
    js_template_rendered = js_template.render(context)
    print 'JS TEMPLATE:\n',js_template
    print 'Jinja:\n',jinja_template
    print 'Js:\n',js_template_rendered
    assert jinja_template == js_template_rendered

def test_case_generator():
    templates = env.list_templates()
    for f in templates:
        yield compare_templates, f

def main():
    """Runs the testsuite as command line application."""
    import nose
    try:
        nose.main(defaultTest="")
    except Exception, e:
        print 'Error: %s' % e

if __name__ == '__main__':
    main()
# for dirname, dirnames, filenames in os.walk(TEMPLATE_FOLDER):



# print gen2('''{% extends "a" %}
# {% block c %}
#   {% for i in x %}{{i}}:::{{loop.index}}
#   {% endfor %}
# {% endblock %}
# {% macro for1(datsa) -%}{{data}}{% endmacro %}
# {% block a %}{{ super() }}
#   {% include "x" %}
#   {{a|capitalize}}
#   a
#   {{for1(s)}}
# {% endblock %}''')

# print gen('''{% extends "a" %}''')
# t = '''{% set s=2 %}{% macro for1(data,dos,tres=3) -%}{{data}}{% set s=3233223 %}{{s}}{% endmacro %}{{for1(1)}}{{s}}'''
# print gen(t)
# template = env.from_string(t)
# print template.render()
# print gen('''{% from a import b %}''')
# print gen2('''{% extends 'a' %}''')


# print gen2('''{% set a = 2*2 or 7 %}{{a}}''')
# print gen2('''{% for a,b in x(c) if a==1 %}{{loop}}{% for s in sa %}{{loop}}{% endfor %}{% else %}s{% endfor %}''')

# filename = '%s%s'%(TEMPLATE_FOLDER,'include.tmpl')
# template_string = open(filename).read()
# code = gen2(template_string, filename)


# with open('runtime.js', 'r') as f:
#     ctx.eval(f.read())

# try:
#   # t = ctx.eval('new (%s)'%code).render(context)
#   t = ctx.eval(code)
#   # print code
#   js_template = ctx.locals.Jinja2.get(filename)
#   # print js_template.module().x(233)
#   s1 = env.from_string(template_string).render(context)
#   s2 = js_template.render(context)
# except Exception, e:
#   print code
#   raise e

# t = ctx.eval('new %s()'%code)
# print t.prototype.root({'vars':{}})
# print gen2('''{% extends 'a' %}{% set p=2 %}''')
# print gen2('''{% extends 'a' %}{% block a %}{{s}}{% endblock %}s{% block r %}{{super}}{% endblock %}''')
# print gen2('''{% set c=True %}{% if d or c %}{{a}}{% else %}{{d}}{% endif %}''')


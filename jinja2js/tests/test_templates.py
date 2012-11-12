#encoding: utf8
import os
# import sys
# path = os.path.abspath(os.path.join(os.path.dirname(__file__),"../../"))
# sys.path.append(path)
import jinja2
import jinja2js
from jinja2js.generate import generate
from nose import with_setup


def setup_func():
    global jinja_env, processors

def teardown_func():
    pass


from pyv8 import PyV8

TEMPLATE_FOLDER = 'templates/'
env = jinja2.Environment(loader = jinja2.FileSystemLoader(TEMPLATE_FOLDER))

class Global(PyV8.JSClass): 
  def log(self,*args):
    print args



ctx = PyV8.JSContext(Global())
ctx.enter()

runtime = os.path.join(os.path.dirname(__file__),"../../jinja2js/lib/runtime.js")
with open(runtime, 'r') as f:
    ctx.eval(f.read())


templates = env.list_templates()

# templates = ['include.tmpl','partials/include.tmpl']
# templates = ['extends.tmpl','partials/layout.tmpl']
for f in templates:
    # filename = TEMPLATE_FOLDER+f
    template_string, filename, _ = env.loader.get_source(env,f)
    code = generate(template_string, f)
    # print code
    ctx.eval(code)

context = {'context':True}


def compare_templates(f):
    print '*'*30
    print f
    print '*'*30
    try:
        jinja_template = env.get_template(f).render(context)
        js_template = ctx.locals.Jinja2.get(f)
        js_template_rendered = js_template.render(context)
        assert jinja_template == js_template_rendered
        print 'Jinja:\n'
        print '_'*30
        print jinja_template
        print '='*30
        print 'Js:\n'
        print '_'*30
        print js_template_rendered
    except AssertionError,e:
        print 'Jinja:\n',jinja_template
        print 'Js:\n',js_template_rendered
        raise e
    except Exception, e:
        print js_template
        raise e
    else:
        print '-'*30
        print 'PASS'
        print '-'*30
        print '\n'

@with_setup(setup_func, teardown_func)
def test_case_generator():
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


import os
import jinja2
from .compiler import generate as _generate

env = jinja2.Environment()

def get_node(env,source):
    return env._parse(source,None,None)

def generate_node(env,node,name):
    return _generate(node,env,name,name)

def generate(env,source,name):
    return generate_node(env,get_node(env,source),name)

def generate_template():
    from optparse import OptionParser
    usage = "usage: %prog [options] file [output]"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    filename = args[0]
    source = open(filename).read()
    print generate(env, source,filename)

def lib(minified=False):
    runtime = os.path.join(os.path.dirname(__file__),"./lib/runtime.min.js" if minified else "./lib/runtime.js")
    with open(runtime, 'r') as f:
        return f.read()

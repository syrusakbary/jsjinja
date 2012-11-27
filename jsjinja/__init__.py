import jinja2
import os
from .compiler import generate

_lib_js = {}

def lib(minified=False):
    global _lib_js
    key = "minified" if minified else "normal"
    if key not in _lib_js:
        runtime = os.path.join(os.path.dirname(__file__),"lib/jinja2.runtime.min.js" if minified else "lib/jinja2.runtime.js")
        _lib_js[key] = open(runtime,'r').read()
    return _lib_js[key]

class JsJinja (object):
    js_environment = 'Jinja2'
    def __init__(self,environment=None):
        self.environment = environment or jinja2.Environment()

    def generate_node(self,node,name):
        return generate(node,self.environment,name,name,env=self.js_environment)

    def generate(self,filename):
        source, fn, _ = self.environment.loader.get_source(self.environment,filename)
        return self._generate(source,filename)

    def _generate(self,source,name):
        node = self.environment._parse(source,name,name)
        return self.generate_node(node,name)

    def generate_all(self):
        templates = self.environment.list_templates()
        return ';\n'.join(map(self.generate,templates))+';'

    def generate_source(self,source,name=None):
        return self._generate(source,name)

    lib = staticmethod(lib)

def generate_template():
    from optparse import OptionParser
    j = JsJinja()

    usage = "usage: %prog [options] file [output]"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    filename = args[0]
    source = open(filename).read()
    print j.generate_source(source, filename)

# j = jsjinja()
# print j.generate('template.tmpl')

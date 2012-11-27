import jinja2
import os
from .compiler import generate
import glob
import re

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
        return ';'+';\n'.join(map(self.generate,templates))+';'

    def generate_source(self,source,name=None):
        return self._generate(source,name)

    lib = staticmethod(lib)

def generate_template():
    from optparse import OptionParser
    j = JsJinja()

    usage = "usage: %prog [options] files"
    parser = OptionParser(usage)
    parser.add_option("-o", "--output", dest="output",default=None,
                  help="write output to FILE", metavar="FILE")
    parser.add_option("-b", "--base", dest="base",default=None,
                  help="Set tempalte dir for dropping it in template name", metavar="FILE")
    parser.add_option("-l", "--lib", dest="lib",default=False,
                  help="Include Jinja2 runtime lib", action="store_true")
    (options, args) = parser.parse_args()

    if not args:
        raise Exception('You must specify input files')

    files = []
    for a in args:
        files += glob.glob(a)

    generated = [lib(True)] if options.lib else []
    for f in files:
        source = open(f).read()
        if options.base:
            f = re.sub('^'+options.base+'/?', '', f)
        gen = j.generate_source(source, f)
        generated.append(gen)

    generated = ';'+';\n'.join(generated)+';'
    output = options.output
    if output:
        with open(output,'w') as f:
            f.write(generated)
    else:
        print generated

# j = jsjinja()
# print j.generate('template.tmpl')

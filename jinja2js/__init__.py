import jinja2
import os
from .compiler import generate

class Jinja2Js (object):
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

def lib(minified=False):
    runtime = os.path.join(os.path.dirname(__file__),"./lib/runtime.min.js" if minified else "./lib/runtime.js")
    with open(runtime, 'r') as f:
        return f.read()

def generate_template():
    from optparse import OptionParser
    j = Jinja2Js()

    usage = "usage: %prog [options] file [output]"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    filename = args[0]
    source = open(filename).read()
    print j.generate_source(source, filename)

# j = Jinja2Js()
# print j.generate('template.tmpl')

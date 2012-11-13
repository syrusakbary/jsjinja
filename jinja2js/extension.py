from jinja2 import nodes
from jinja2.ext import Extension
from generate import generate, generate_node

class Jinja2JsExtension(Extension):
    # a set of names that trigger the extension.
    tags = set(['jinja2js'])

    def __init__(self, environment):
        super(Jinja2JsExtension, self).__init__(environment)

        # add the defaults to the environment
        environment.extend(
            generate_js=self.generate_js
        )
        
    def generate_js(self, source, name=None):
        return generate(self.environment, source, name)

    def parse(self, parser):
        parser.stream.next().lineno #lineno = 
        body = parser.parse_statements(['name:endjinja2js'], drop_needle=True)
        node = nodes.Template(body,lineno=1)
        code = generate_node(self.environment,node or body[0],None)
        return nodes.Output([nodes.Const(code)]).set_lineno(1)

    # def a(self,*args,**kwargs):
    #     return repr(args)+repr(kwargs)
    # #     # print type(body[0])
    # #     # lineno, body
    # #     node = nodes.Template(body,lineno=1)
    # #     generate_node(self.environment,node,'<none>')

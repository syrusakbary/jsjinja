from jinja2 import nodes
from jinja2.ext import Extension
from jsjinja import JsJinja
# from generate import generate, generate_js, generate_node, generate_all_templates

class JsJinjaExtension(Extension):
    # a set of names that trigger the extension.
    tags = set(['jsjinja'])

    def __init__(self, environment):
        super(JsJinjaExtension, self).__init__(environment)

        # add the defaults to the environment
        environment.extend(
            jsjinja=JsJinja(self.environment)
            # generate_js=self.generate_js,
            # generate_all_templates=self.generate_all_templates,
        )
        
    # def generate_js(self, name=None, source=None):
    #     if not source and not name:
    #         raise Exception("You must specity the name or source (...).generate_js([name|source]=...)")
    #     if not source:
    #         source = generate_js(self.environment, name)
    #     return generate(self.environment, source, name)

    # def generate_all_templates(self):
    #     return generate_all_templates(self.environment)

    def parse(self, parser):
        parser.stream.next().lineno # lineno = 
        body = parser.parse_statements(['name:endjsjinja'], drop_needle=True)
        node = nodes.Template(body,lineno=1)
        code = self.environment.jsjinja.generate_node(node or body[0],None)
        return nodes.Output([nodes.Const(code)]).set_lineno(1)

    # def a(self,*args,**kwargs):
    #     return repr(args)+repr(kwargs)
    # #     # print type(body[0])
    # #     # lineno, body
    # #     node = nodes.Template(body,lineno=1)
    # #     generate_node(self.environment,node,'<none>')

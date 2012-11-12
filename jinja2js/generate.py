from .compiler import generate as _generate
import jinja2

env = jinja2.Environment()

def generate(source,name):
    return _generate(env._parse(source,None,None),env,name,name)

def generate_template():
    from optparse import OptionParser
    usage = "usage: %prog [options] file [output]"
    parser = OptionParser(usage)
    (options, args) = parser.parse_args()
    filename = args[0]
    source = open(filename).read()
    print generate(source,filename)
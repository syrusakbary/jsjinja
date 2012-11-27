# -*- coding: utf-8 -*-
"""
    jinja2.compiler
    ~~~~~~~~~~~~~~~

    Compiles nodes into python code.

    :copyright: (c) 2012 by Syrus Akbary.
    :license: BSD, see LICENSE for more details.
"""
from cStringIO import StringIO
from itertools import chain
from copy import deepcopy
from jinja2 import nodes
from jinja2.nodes import EvalContext
from jinja2.visitor import NodeVisitor
from jinja2.exceptions import TemplateAssertionError
from jinja2.utils import Markup, concat, escape, is_python_keyword, next

operators = {
    'eq':       '==',
    'ne':       '!=',
    'gt':       '>',
    'gteq':     '>=',
    'lt':       '<',
    'lteq':     '<=',
    'in':       'in',
    'notin':    'not in'
}

try:
    exec '(0 if 0 else 0)'
except SyntaxError:
    have_condexpr = False
else:
    have_condexpr = True


# what method to iterate over items do we want to use for dict iteration
# in generated code?  on 2.x let's go with iteritems, on 3.x with items
if hasattr(dict, 'iteritems'):
    dict_item_iter = 'iteritems'
else:
    dict_item_iter = 'items'


# does if 0: dummy(x) get us x into the scope?
def unoptimize_before_dead_code():
    x = 42
    def f():
        if 0: dummy(x)
    return f
unoptimize_before_dead_code = bool(unoptimize_before_dead_code().func_closure)


def generate(node, environment, name, filename, stream=None,
             defer_init=False, env=None):
    """Generate the python source for a node tree."""
    # if not isinstance(node, nodes.Template):
    #     raise TypeError('Can\'t compile non template nodes')
    generator = CodeGenerator(environment, name, filename, stream, defer_init)
    # generator.visit(node)
    if isinstance(node, nodes.Template):
        generator.visit(node, environment=env)
    else:
        eval_ctx = EvalContext(environment, name)
        frame = Frame(eval_ctx)
        generator.visit(node, frame=frame)
    if stream is None:
        return generator.stream.getvalue()


def has_safe_repr(value):
    """Does the node have a safe representation?"""
    if value is None or value is NotImplemented or value is Ellipsis:
        return True
    if isinstance(value, (bool, int, long, float, complex, basestring,
                          xrange, Markup)):
        return True
    if isinstance(value, (tuple, list, set, frozenset)):
        for item in value:
            if not has_safe_repr(item):
                return False
        return True
    elif isinstance(value, dict):
        for key, value in value.iteritems():
            if not has_safe_repr(key):
                return False
            if not has_safe_repr(value):
                return False
        return True
    return False


def find_undeclared(nodes, names):
    """Check if the names passed are accessed undeclared.  The return value
    is a set of all the undeclared names from the sequence of names found.
    """
    visitor = UndeclaredNameVisitor(names)
    try:
        for node in nodes:
            visitor.visit(node)
    except VisitorExit:
        pass
    return visitor.undeclared


class Identifiers(object):
    """Tracks the status of identifiers in frames."""

    def __init__(self):
        # variables that are known to be declared (probably from outer
        # frames or because they are special for the frame)
        self.declared = set()

        # undeclared variables from outer scopes
        self.outer_undeclared = set()

        # names that are accessed without being explicitly declared by
        # this one or any of the outer scopes.  Names can appear both in
        # declared and undeclared.
        self.undeclared = set()

        # names that are declared locally
        self.declared_locally = set()

        # names that are declared by parameters
        self.declared_parameter = set()

    def add_special(self, name):
        """Register a special name like `loop`."""
        self.undeclared.discard(name)
        self.declared.add(name)

    def is_declared(self, name):
        """Check if a name is declared in this or an outer scope."""
        if name in self.declared_locally or name in self.declared_parameter:
            return True
        return name in self.declared

    def copy(self):
        return deepcopy(self)


class Frame(object):
    """Holds compile time information for us."""

    def __init__(self, eval_ctx, parent=None):
        self.eval_ctx = eval_ctx
        self.identifiers = Identifiers()

        # a toplevel frame is the root + soft frames such as if conditions.
        self.toplevel = False

        # the root frame is basically just the outermost frame, so no if
        # conditions.  This information is used to optimize inheritance
        # situations.
        self.rootlevel = False

        # in some dynamic inheritance situations the compiler needs to add
        # write tests around output statements.
        self.require_output_check = parent and parent.require_output_check

        # inside some tags we are using a buffer rather than yield statements.
        # this for example affects {% filter %} or {% macro %}.  If a frame
        # is buffered this variable points to the name of the list used as
        # buffer.
        self.buffer = None

        # the name of the block we're in, otherwise None.
        self.block = parent and parent.block or None

        # a set of actually assigned names
        self.assigned_names = set()

        # the parent of this frame
        self.parent = parent

        if parent is not None:
            self.identifiers.declared.update(
                parent.identifiers.declared |
                parent.identifiers.declared_parameter |
                parent.assigned_names
            )
            self.identifiers.outer_undeclared.update(
                parent.identifiers.undeclared -
                self.identifiers.declared
            )
            self.buffer = parent.buffer

    def copy(self):
        """Create a copy of the current one."""
        rv = object.__new__(self.__class__)
        rv.__dict__.update(self.__dict__)
        rv.identifiers = object.__new__(self.identifiers.__class__)
        rv.identifiers.__dict__.update(self.identifiers.__dict__)
        return rv

    def inspect(self, nodes):
        """Walk the node and check for identifiers.  If the scope is hard (eg:
        enforce on a python level) overrides from outer scopes are tracked
        differently.
        """
        visitor = FrameIdentifierVisitor(self.identifiers)
        for node in nodes:
            visitor.visit(node)

    def find_shadowed(self, extra=()):
        """Find all the shadowed names.  extra is an iterable of variables
        that may be defined with `add_special` which may occour scoped.
        """
        i = self.identifiers
        return (i.declared | i.outer_undeclared) & \
               (i.declared_locally | i.declared_parameter) | \
               set(x for x in extra if i.is_declared(x))

    def inner(self):
        """Return an inner frame."""
        return Frame(self.eval_ctx, self)

    def soft(self):
        """Return a soft frame.  A soft frame may not be modified as
        standalone thing as it shares the resources with the frame it
        was created of, but it's not a rootlevel frame any longer.
        """
        rv = self.copy()
        rv.rootlevel = False
        return rv

    __copy__ = copy


class VisitorExit(RuntimeError):
    """Exception used by the `UndeclaredNameVisitor` to signal a stop."""


class DependencyFinderVisitor(NodeVisitor):
    """A visitor that collects filter and test calls."""

    def __init__(self):
        self.filters = set()
        self.tests = set()

    def visit_Filter(self, node):
        self.generic_visit(node)
        self.filters.add(node.name)

    def visit_Test(self, node):
        self.generic_visit(node)
        self.tests.add(node.name)

    def visit_Block(self, node):
        """Stop visiting at blocks."""


class UndeclaredNameVisitor(NodeVisitor):
    """A visitor that checks if a name is accessed without being
    declared.  This is different from the frame visitor as it will
    not stop at closure frames.
    """

    def __init__(self, names):
        self.names = set(names)
        self.undeclared = set()

    def visit_Name(self, node):
        if node.ctx == 'load' and node.name in self.names:
            self.undeclared.add(node.name)
            if self.undeclared == self.names:
                raise VisitorExit()
        else:
            self.names.discard(node.name)

    def visit_Block(self, node):
        """Stop visiting a blocks."""


class FrameIdentifierVisitor(NodeVisitor):
    """A visitor for `Frame.inspect`."""

    def __init__(self, identifiers):
        self.identifiers = identifiers

    def visit_Name(self, node):
        """All assignments to names go through this function."""
        if node.ctx == 'store':
            self.identifiers.declared_locally.add(node.name)
        elif node.ctx == 'param':
            self.identifiers.declared_parameter.add(node.name)
        elif node.ctx == 'load' and not \
             self.identifiers.is_declared(node.name):
            self.identifiers.undeclared.add(node.name)

    def visit_If(self, node):
        self.visit(node.test)
        real_identifiers = self.identifiers

        old_names = real_identifiers.declared_locally | \
                    real_identifiers.declared_parameter

        def inner_visit(nodes):
            if not nodes:
                return set()
            self.identifiers = real_identifiers.copy()
            for subnode in nodes:
                self.visit(subnode)
            rv = self.identifiers.declared_locally - old_names
            # we have to remember the undeclared variables of this branch
            # because we will have to pull them.
            real_identifiers.undeclared.update(self.identifiers.undeclared)
            self.identifiers = real_identifiers
            return rv

        body = inner_visit(node.body)
        else_ = inner_visit(node.else_ or ())

        # the differences between the two branches are also pulled as
        # undeclared variables
        real_identifiers.undeclared.update(body.symmetric_difference(else_) -
                                           real_identifiers.declared)

        # remember those that are declared.
        real_identifiers.declared_locally.update(body | else_)

    def visit_Macro(self, node):
        self.identifiers.declared_locally.add(node.name)

    def visit_Import(self, node):
        self.generic_visit(node)
        self.identifiers.declared_locally.add(node.target)

    def visit_FromImport(self, node):
        self.generic_visit(node)
        for name in node.names:
            if isinstance(name, tuple):
                self.identifiers.declared_locally.add(name[1])
            else:
                self.identifiers.declared_locally.add(name)

    def visit_Assign(self, node):
        """Visit assignments in the correct order."""
        self.visit(node.node)
        self.visit(node.target)

    def visit_For(self, node):
        """Visiting stops at for blocks.  However the block sequence
        is visited as part of the outer scope.
        """
        self.visit(node.iter)

    def visit_CallBlock(self, node):
        self.visit(node.call)

    def visit_FilterBlock(self, node):
        self.visit(node.filter)

    def visit_Scope(self, node):
        """Stop visiting at scopes."""

    def visit_Block(self, node):
        """Stop visiting at blocks."""


class CompilerExit(Exception):
    """Raised if the compiler encountered a situation where it just
    doesn't make sense to further process the code.  Any block that
    raises such an exception is not further processed.
    """

import simplejson

class JSVar(object):
    def __init__(self,var): self.var = var

    def __repr__(self): return simplejson.dumps(self.var)
    
class CodeGenerator(NodeVisitor):

    def __init__(self, environment, name, filename, stream=None,
                 defer_init=False):
        if stream is None:
            stream = StringIO()
        self.environment = environment
        self.name = name
        self.filename = filename
        self.stream = stream
        self.created_block_context = False
        self.defer_init = defer_init

        # aliases for imports
        self.import_aliases = {}

        # a registry for all blocks.  Because blocks are moved out
        # into the global python scope they are registered here
        self.blocks = {}

        # the number of extends statements so far
        self.extends_so_far = 0

        # some templates have a rootlevel extends.  In this case we
        # can safely assume that we're a child template and do some
        # more optimizations.
        self.has_known_extends = False

        # the current line number
        self.code_lineno = 1

        # registry of all filters and tests (global, not block local)
        self.tests = {}
        self.filters = {}

        # the debug information
        self.debug_info = []
        self._write_debug_info = None

        # the number of new lines before the next write()
        self._new_lines = 0

        # the line number of the last written statement
        self._last_line = 0

        # true if nothing was written so far.
        self._first_write = True

        # used by the `temporary_identifier` method to get new
        # unique, temporary identifier
        self._last_identifier = 0

        # the current indentation
        self._indentation = 0

    # -- Various compilation helpers

    def fail(self, msg, lineno):
        """Fail with a :exc:`TemplateAssertionError`."""
        raise TemplateAssertionError(msg, lineno, self.name, self.filename)

    def temporary_identifier(self):
        """Get a new unique identifier."""
        self._last_identifier += 1
        return 't_%d' % self._last_identifier

    def buffer(self, frame):
        """Enable buffering for the frame from that point onwards."""
        frame.buffer = self.temporary_identifier()
        self.writeline('var %s = "";' % frame.buffer)

    def return_buffer_contents(self, frame):
        """Return the buffer contents of the frame."""
        if frame.eval_ctx.volatile:
            self.writeline('if context.eval_ctx.autoescape ')
            self.indent()
            self.writeline('return escape(%s);' % frame.buffer)
            self.outdent()
            self.writeline('else ')
            self.indent()
            self.writeline('return %s;' % frame.buffer)
            self.outdent()
        elif frame.eval_ctx.autoescape:
            self.writeline('return escape(%s);' % frame.buffer)
        else:
            self.writeline('return %s;' % frame.buffer)

    def indent(self):
        """Indent by one."""
        self.write('{')
        self._indentation += 1

    def outdent(self, step=1):
        """Outdent by step."""
        for i in xrange(step):
            self._indentation -= 1
            self.writeline('}')

    def start_write(self, frame, node=None):
        """Yield or write into the frame buffer."""
        if frame.buffer is None:
            self.writeline('buf += ', node)
        else:
            self.writeline('%s += (' % frame.buffer, node)

    def end_write(self, frame):
        """End the writing process started by `start_write`."""
        if frame.buffer is not None:
            self.write(')')

    def simple_write(self, s, frame, node=None):
        """Simple shortcut for start_write + write + end_write."""
        self.start_write(frame, node)
        self.write(s)
        self.end_write(frame)

    def blockvisit(self, nodes, frame):
        """Visit a list of nodes as block in a frame.  If the current frame
        is no buffer a dummy ``if 0: yield None`` is written automatically
        unless the force_generator parameter is set to False.
        """
        # if frame.buffer is None:
        #     self.writeline('if 0: yield None')
        # else:
        #     self.writeline('pass')
        try:
            for node in nodes:
                self.visit(node, frame)
        except CompilerExit:
            pass

    def write(self, x):
        """Write a string into the output stream."""
        if self._new_lines:
            if not self._first_write:
                self.stream.write('\n' * self._new_lines)
                self.code_lineno += self._new_lines
                if self._write_debug_info is not None:
                    self.debug_info.append((self._write_debug_info,
                                            self.code_lineno))
                    self._write_debug_info = None
            self._first_write = False
            self.stream.write('    ' * self._indentation)
            self._new_lines = 0
        self.stream.write(x)

    def writeline(self, x, node=None, extra=0):
        """Combination of newline and write."""
        self.newline(node, extra)
        self.write(x)

    def newline(self, node=None, extra=0):
        """Add one or more newlines before the next write."""
        self._new_lines = max(self._new_lines, 1 + extra)
        if node is not None and node.lineno != self._last_line:
            self._write_debug_info = node.lineno
            self._last_line = node.lineno

    def signature(self, node, frame, extra_kwargs=None):
        """Writes a function call to the stream for the current node.
        A leading comma is added automatically.  The extra keyword
        arguments may not include python keywords otherwise a syntax
        error could occour.  The extra keyword arguments should be given
        as python dict.
        """
        # if any of the given keyword arguments is a python keyword
        # we have to make sure that no invalid call is created.
        kwarg_workaround = False
        for kwarg in chain((x.key for x in node.kwargs), extra_kwargs or ()):
            if is_python_keyword(kwarg):
                kwarg_workaround = True
                break

        self.write(', [')

        for arg in node.args:
            self.visit(arg, frame)
            self.write(', ')
        self.write(']')

        if not kwarg_workaround:
            self.write(', {')
            for kwarg in node.kwargs:
                self.visit(kwarg, frame)
                self.write(', ')
            self.write('}')
            if extra_kwargs is not None:
                for key, value in extra_kwargs.iteritems():
                    self.write(', %s=%s' % (key, value))
        if node.dyn_args:
            self.write(', *')
            self.visit(node.dyn_args, frame)

        if kwarg_workaround:
            if node.dyn_kwargs is not None:
                self.write(', **dict({')
            else:
                self.write(', **{')
            for kwarg in node.kwargs:
                self.write('%r: ' % kwarg.key)
                self.visit(kwarg.value, frame)
                self.write(', ')
            if extra_kwargs is not None:
                for key, value in extra_kwargs.iteritems():
                    self.write('%r: %s, ' % (JSVar(key), value))
            if node.dyn_kwargs is not None:
                self.write('}, **')
                self.visit(node.dyn_kwargs, frame)
                self.write(')')
            else:
                self.write('}')

        elif node.dyn_kwargs is not None:
            self.write(', **')
            self.visit(node.dyn_kwargs, frame)

    def pull_locals(self, frame):
        """Pull all the references identifiers into the local scope."""
        for name in frame.identifiers.undeclared:
            self.writeline('var l_%s = context.resolve(%r);' % (name, JSVar(name)))

    def pull_dependencies(self, nodes):
        """Pull all the dependencies."""
        visitor = DependencyFinderVisitor()
        for node in nodes:
            visitor.visit(node)
        for dependency in 'filters', 'tests':
            mapping = getattr(self, dependency)
            for name in getattr(visitor, dependency):
                if name not in mapping:
                    mapping[name] = self.temporary_identifier()
                self.writeline('%s = Jinja2.%s[%r]' %
                               (mapping[name], dependency, JSVar(name)))

    def unoptimize_scope(self, frame):
        """Disable Python optimizations for the frame."""
        # XXX: this is not that nice but it has no real overhead.  It
        # mainly works because python finds the locals before dead code
        # is removed.  If that breaks we have to add a dummy function
        # that just accepts the arguments and does nothing.
        if frame.identifiers.declared:
            self.writeline('%sdummy(%s)' % (
                unoptimize_before_dead_code and 'if (false)  ' or '',
                ', '.join('l_' + name for name in frame.identifiers.declared)
            ))

    def push_scope(self, frame, extra_vars=()):
        """This function returns all the shadowed variables in a dict
        in the form name: alias and will write the required assignments
        into the current scope.  No indentation takes place.

        This also predefines locally declared variables from the loop
        body because under some circumstances it may be the case that

        `extra_vars` is passed to `Frame.find_shadowed`.
        """
        aliases = {}
        for name in frame.find_shadowed(extra_vars):
            aliases[name] = ident = self.temporary_identifier()
            self.writeline('var %s = l_%s;' % (ident, name))
        to_declare = set()
        for name in frame.identifiers.declared_locally:
            if name not in aliases:
                to_declare.add('var l_' + name)
        if to_declare:
            self.writeline(' = '.join(to_declare) + ' = undefined;')
        return aliases

    def pop_scope(self, aliases, frame):
        """Restore all aliases and delete unused variables."""
        for name, alias in aliases.iteritems():
            self.writeline('var l_%s = %s;' % (name, alias))
        to_delete = set()
        for name in frame.identifiers.declared_locally:
            if name not in aliases:
                to_delete.add('l_' + name)
        if to_delete:
            # we cannot use the del statement here because enclosed
            # scopes can trigger a SyntaxError:
            #   a = 42; b = lambda: a; del a
            self.writeline(' = '.join(to_delete) + ' = undefined;')

    def function_scoping(self, node, frame, children=None,
                         find_special=True):
        """In Jinja a few statements require the help of anonymous
        functions.  Those are currently macros and call blocks and in
        the future also recursive loops.  As there is currently
        technical limitation that doesn't allow reading and writing a
        variable in a scope where the initial value is coming from an
        outer scope, this function tries to fall back with a common
        error message.  Additionally the frame passed is modified so
        that the argumetns are collected and callers are looked up.

        This will return the modified frame.
        """
        # we have to iterate twice over it, make sure that works
        if children is None:
            children = node.iter_child_nodes()
        children = list(children)
        func_frame = frame.inner()
        func_frame.inspect(children)

        # variables that are undeclared (accessed before declaration) and
        # declared locally *and* part of an outside scope raise a template
        # assertion error. Reason: we can't generate reasonable code from
        # it without aliasing all the variables.
        # this could be fixed in Python 3 where we have the nonlocal
        # keyword or if we switch to bytecode generation
        overriden_closure_vars = (
            func_frame.identifiers.undeclared &
            func_frame.identifiers.declared &
            (func_frame.identifiers.declared_locally |
             func_frame.identifiers.declared_parameter)
        )
        if overriden_closure_vars:
            self.fail('It\'s not possible to set and access variables '
                      'derived from an outer scope! (affects: %s)' %
                      ', '.join(sorted(overriden_closure_vars)), node.lineno)

        # remove variables from a closure from the frame's undeclared
        # identifiers.
        func_frame.identifiers.undeclared -= (
            func_frame.identifiers.undeclared &
            func_frame.identifiers.declared
        )

        # no special variables for this scope, abort early
        if not find_special:
            return func_frame

        func_frame.accesses_kwargs = False
        func_frame.accesses_varargs = False
        func_frame.accesses_caller = False
        func_frame.arguments = args = ['l_' + x.name for x in node.args]

        undeclared = find_undeclared(children, ('caller', 'kwargs', 'varargs'))

        if 'caller' in undeclared:
            func_frame.accesses_caller = True
            func_frame.identifiers.add_special('caller')
            args.append('l_caller')
        if 'kwargs' in undeclared:
            func_frame.accesses_kwargs = True
            func_frame.identifiers.add_special('kwargs')
            args.append('l_kwargs')
        if 'varargs' in undeclared:
            func_frame.accesses_varargs = True
            func_frame.identifiers.add_special('varargs')
            args.append('l_varargs')
        return func_frame

    def macro_body(self, node, frame, children=None, defaults={}):
        """Dump the function def of a macro or call block."""
        frame = self.function_scoping(node, frame, children)
        # macros are delayed, they never require output checks
        frame.require_output_check = False
        args = frame.arguments
        # XXX: this is an ugly fix for the loop nesting bug
        # (tests.test_old_bugs.test_loop_call_bug).  This works around
        # a identifier nesting problem we have in general.  It's just more
        # likely to happen in loops which is why we work around it.  The
        # real solution would be "nonlocal" all the identifiers that are
        # leaking into a new python frame and might be used both unassigned
        # and assigned.
        if 'loop' in frame.identifiers.declared:
            args = args + ['l_loop=l_loop']
        self.writeline('var l_%s = function (%s) ' % (node.name, ', '.join(args)), node)
        self.indent()
        for kw_name,_ in defaults.items():
            self.writeline('if (typeof l_%(name)s == \'undefined\') l_%(name)s = arguments.callee.__defaults__.%(name)s;'%{'name':kw_name})
        self.buffer(frame)
        self.pull_locals(frame)
        self.blockvisit(node.body, frame)
        self.return_buffer_contents(frame)
        self.outdent()
        return frame

    def get_defaults(self,node):
        defaults = {}
        l = len(node.defaults)
        for i, d in enumerate(node.defaults):
            kwarg_name = node.args[-l+i].name
            defaults[kwarg_name] = d.value
        return defaults

    def macro_def(self, node, frame, defaults={}):
        """Dump the macro definition for the def created by macro_body."""
        arg_tuple = ', '.join(repr(JSVar(x.name)) for x in node.args)
        name = getattr(node, 'name', None)

        self.writeline('l_%s.__args__ = [%s];' %
                   (name, arg_tuple))
        self.writeline('l_%s.__defaults__ = %r;' %
                   (name, JSVar(defaults)))

        # self.write('], %r, %r, %r)' % (
        #     JSVar(bool(frame.accesses_kwargs)),
        #     JSVar(bool(frame.accesses_varargs)),
        #     JSVar(bool(frame.accesses_caller))
        # ))

    def position(self, node):
        """Return a human readable position for the node."""
        rv = 'line %d' % node.lineno
        if self.name is not None:
            rv += ' in ' + repr(self.name)
        return rv

    def initbuffer(self):
        self.writeline('var buf = "";')

    def returnbuffer(self):
        self.writeline('return buf;')
    # -- Statement Visitors

    def visit_Template(self, node, frame=None, environment=None):
        assert frame is None, 'no root frame allowed'
        eval_ctx = EvalContext(self.environment, self.name)
        # if not unoptimize_before_dead_code:
        #     self.writeline('var dummy = function() {};')

        # if we want a deferred initialization we cannot move the
        # environment into a local name
        envenv = not self.defer_init and ', Jinja2' or ''

        # do we have an extends tag at all?  If not, we can save some
        # overhead by just not processing any inheritance code.
        have_extends = node.find(nodes.Extends) is not None

        # find all blocks
        for block in node.find_all(nodes.Block):
            if block.name in self.blocks:
                self.fail('block %r defined twice' % JSVar(block.name), block.lineno)
            self.blocks[block.name] = block

        # find all imports and import them
        for import_ in node.find_all(nodes.ImportedName):
            if import_.importname not in self.import_aliases:
                imp = import_.importname
                self.import_aliases[imp] = alias = self.temporary_identifier()
                if '.' in imp:
                    module, obj = imp.rsplit('.', 1)
                    self.writeline('from %s import %s as %s' %
                                   (module, obj, alias))
                else:
                    self.writeline('import %s as %s' % (imp, alias))

        # add the load name
        template_name = JSVar(self.name)
        self.writeline('(function() ')
        self.indent()
        self.writeline('/* %s */' % self.name)
        self.writeline('Jinja2.extends(Template, Jinja2.Template);')
        if self.name:
            self.writeline('Jinja2.registerTemplate(%r, Template);' % template_name)
        self.writeline('function Template() {return Template.__super__.constructor.apply(this, arguments);};')
        # self.indent()
        # self.writeline('environment = environment;')
        # self.outdent()
        self.writeline('Template.prototype.root = function (context) ')
        # process the root
        frame = Frame(eval_ctx)
        frame.inspect(node.body)
        frame.toplevel = frame.rootlevel = True
        frame.require_output_check = have_extends and not self.has_known_extends
        self.indent()
        # self.writeline('environment = this.environment;')
        self.initbuffer();
        # if have_extends:
        #     self.writeline('var parent_template;')
        if 'self' in find_undeclared(node.body, ('self',)):
            frame.identifiers.add_special('self')
            self.writeline('l_self = Jinja2.TemplateReference(context)')
        self.pull_locals(frame)
        self.pull_dependencies(node.body)
        self.blockvisit(node.body, frame)
        # make sure that the parent root is called.
        if have_extends:
            if not self.has_known_extends:
                self.writeline('if (parent_template) ')
                self.indent()                
            self.writeline('buf += parent_template.root(context);')
            # self.outdent((not self.has_known_extends))
        # at this point we now have the blocks collected and can visit them too.
        self.returnbuffer()
        self.outdent()

        for name, block in self.blocks.iteritems():
            block_frame = Frame(eval_ctx)
            block_frame.inspect(block.body)
            block_frame.block = name
            self.writeline('Template.prototype.block_%s = function (context) ' % (name),
                           block)
            self.indent()
            self.initbuffer()
            undeclared = find_undeclared(block.body, ('self', 'super'))
            if 'self' in undeclared:
                block_frame.identifiers.add_special('self')
                self.writeline('var l_self = Jinja2.TemplateReference(context)')
            if 'super' in undeclared:
                block_frame.identifiers.add_special('super')
                # self.writeline('log(context);')
                self.writeline('var l_super = context.super(%r, '
                               'Template.prototype.block_%s)' % (JSVar(name), name))
            self.pull_locals(block_frame)
            self.pull_dependencies(block.body)
            self.blockvisit(block.body, block_frame)
            self.returnbuffer()
            self.outdent()

        self.writeline('return Template;')
        self.outdent()
        self.write(')()')
        # self.writeline('blocks = {%s}' % ', '.join('%r: block_%s' % (x, x)
        #                                            for x in self.blocks),
        #                extra=1)

        # add a function that returns the debug info
        # self.writeline('debug_info = %r' % '&'.join('%s=%s' % x for x
        #                                             in self.debug_info))

    def visit_Block(self, node, frame):
        """Call a block and register it for the template."""
        level = 1
        if frame.toplevel:
            # if we know that we are a child template, there is no need to
            # check if we are one
            if self.has_known_extends:
                return
            if self.extends_so_far > 0:
                self.writeline('if parent_template is None:')
                self.indent()
                level += 1
        context = node.scoped and 'context.derived(locals())' or 'context'
        self.writeline('buf += context.blocks[%r][0](%s);' % (
                       node.name, context), node)

    def visit_Extends(self, node, frame):
        """Calls the extender."""
        if not frame.toplevel:
            self.fail('cannot use extend from a non top-level scope',
                      node.lineno)

        # if the number of extends statements in general is zero so
        # far, we don't have to add a check if something extended
        # the template before this one.
        if self.extends_so_far > 0:

            # if we have a known extends we just add a template runtime
            # error into the generated code.  We could catch that at compile
            # time too, but i welcome it not to confuse users by throwing the
            # same error at different times just "because we can".
            if not self.has_known_extends:
                self.writeline('if parent_template is not None:')
                self.indent()
            self.writeline('raise TemplateRuntimeError(%r)' %
                           'extended multiple times')
            self.outdent()

            # if we have a known extends already we don't need that code here
            # as we know that the template execution will end here.
            if self.has_known_extends:
                raise CompilerExit()

        self.writeline('var parent_template = Jinja2.getTemplate(', node)
        self.visit(node.template, frame)
        self.write(', %r);' % JSVar(self.name))
        self.writeline('for (name in parent_template.blocks) ')
        self.indent()
        self.writeline('var parent_block = parent_template.blocks[name];')
        self.writeline('context.blocks[name] = context.blocks[name] || [];')
        self.writeline('context.blocks[name].push(parent_block)')
        self.outdent()

        # if this extends statement was in the root level we can take
        # advantage of that information and simplify the generated code
        # in the top level from this point onwards
        if frame.rootlevel:
            self.has_known_extends = True

        # and now we have one more
        self.extends_so_far += 1

    def visit_Include(self, node, frame):
        """Handles includes."""
        if node.with_context:
            self.unoptimize_scope(frame)
        if node.ignore_missing:
            self.writeline('try ')
            self.indent()

        func_name = 'get_or_select_template'
        if isinstance(node.template, nodes.Const):
            if isinstance(node.template.value, basestring):
                func_name = 'getTemplate'
            elif isinstance(node.template.value, (tuple, list)):
                func_name = 'selectTemplate'
        elif isinstance(node.template, (nodes.Tuple, nodes.List)):
            func_name = 'selectTemplate'

        self.writeline('template = Jinja2.%s(' % func_name, node)
        self.visit(node.template, frame)
        self.write(', %r)' % JSVar(self.name))
        if node.ignore_missing:
            self.outdent()
            self.writeline('catch (e) {}')
            self.writeline('else ')
            self.indent()

        if node.with_context:
            self.simple_write('template.root(context)', frame)
            # self.writeline('for event in template.root_render_func('
            #                'template.new_context(context.parent, True, '
            #                'locals())):')
        else:
            self.writeline('for event in template.module._body_stream:')

        # self.indent()
        # self.simple_write('event', frame)
        # self.outdent()

        if node.ignore_missing:
            self.outdent()

    def visit_Import(self, node, frame):
        """Visit regular imports."""
        if node.with_context:
            self.unoptimize_scope(frame)
        self.writeline('var l_%s = ' % node.target, node)
        # self.write(';')
        if frame.toplevel:
            self.write('context.vars[%r] = ' % node.target)
        self.write('Jinja2.getTemplate(')
        self.visit(node.template, frame)
        self.write(', %r).' % self.name)
        if node.with_context:
            self.write('make_module(context.parent, True, locals())')
        else:
            self.write('module()')
        if frame.toplevel and not node.target.startswith('_'):
            self.writeline('context.exported_vars.remove(%r);' % node.target)
        frame.assigned_names.add(node.target)

    def visit_FromImport(self, node, frame):
        """Visit named imports."""
        self.newline(node)
        self.write('var included_template = Jinja2.getTemplate(')
        self.visit(node.template, frame)
        self.write(', %r).' % self.name)
        if node.with_context:
            self.write('make_module(context.parent, True)')
        else:
            self.write('module()')
        self.write(';')
        var_names = []
        discarded_names = []
        for name in node.names:
            if isinstance(name, tuple):
                name, alias = name
            else:
                alias = name
            self.writeline('var l_%s = included_template['
                           '%r]' % (alias, name))
            self.writeline('if (typeof l_%s == "undefined")' % alias)
            self.indent()
            self.writeline('l_%s = Jinja2.undefined(%r %% '
                           'included_template.__name__, '
                           'name=%r)' %
                           (alias, 'the template %%r (imported on %s) does '
                           'not export the requested name %s' % (
                                self.position(node),
                                repr(name)
                           ), name))
            self.outdent()
            if frame.toplevel:
                var_names.append(alias)
                if not alias.startswith('_'):
                    discarded_names.append(alias)
            frame.assigned_names.add(alias)

        if var_names:
            if len(var_names) == 1:
                name = var_names[0]
                self.writeline('context.vars[%r] = l_%s' % (name, name))
            else:
                self.writeline('context.vars.update({%s})' % ', '.join(
                    '%r: l_%s' % (name, name) for name in var_names
                ))
        if discarded_names:
            if len(discarded_names) == 1:
                self.writeline('context.exported_vars.remove(%r);' %
                               discarded_names[0])
            else:
                self.writeline('context.exported_vars.difference_'
                               'update((%s));' % ', '.join(map(repr, discarded_names)))

    def visit_For(self, node, frame):
        # when calculating the nodes for the inner frame we have to exclude
        # the iterator contents from it
        children = node.iter_child_nodes(exclude=('iter',))
        if node.recursive:
            loop_frame = self.function_scoping(node, frame, children,
                                               find_special=False)
        else:
            loop_frame = frame.inner()
            loop_frame.inspect(children)

        # try to figure out if we have an extended loop.  An extended loop
        # is necessary if the loop is in recursive mode if the special loop
        # variable is accessed in the body.
        extended_loop = node.recursive or 'loop' in \
                        find_undeclared(node.iter_child_nodes(
                            only=('body',)), ('loop',))

        # if we don't have an recursive loop we have to find the shadowed
        # variables at that point.  Because loops can be nested but the loop
        # variable is a special one we have to enforce aliasing for it.
        if not node.recursive:
            aliases = self.push_scope(loop_frame, ('loop',))

        # otherwise we set up a buffer and add a function def
        else:
            self.writeline('var loop = function(reciter, loop_render_func):', node)
            self.indent()
            self.buffer(loop_frame)
            aliases = {}

        # make sure the loop variable is a special one and raise a template
        # assertion error if a loop tries to write to loop
        if extended_loop:
            loop_frame.identifiers.add_special('loop')
        for name in node.find_all(nodes.Name):
            if name.ctx == 'store' and name.name == 'loop':
                self.fail('Can\'t assign to special loop variable '
                          'in for-loop target', name.lineno)

        self.pull_locals(loop_frame)
        if node.else_:
            iteration_indicator = self.temporary_identifier()
            self.writeline('var %s = 1;' % iteration_indicator)

        # Create a fake parent loop if the else or test section of a
        # loop is accessing the special loop variable and no parent loop
        # exists.
        if 'loop' not in aliases and 'loop' in find_undeclared(
           node.iter_child_nodes(only=('else_', 'test')), ('loop',)):
            self.writeline("l_loop = Jinja2.undefined(%r, name='loop')" %
                ("'loop' is undefined. the filter section of a loop as well "
                 "as the else block don't have access to the special 'loop'"
                 " variable of the current loop.  Because there is no parent "
                 "loop it's undefined.  Happened in loop on %s" %
                 self.position(node)))

        if isinstance(node.target,nodes.Name):
            loop_vars = [node.target.name]
        else:
            loop_vars = [n.name for n in node.target.find_all(nodes.Name)]

        # self.writeline(str(loop_vars))
        loop_frame.identifiers.declared.add(*loop_vars)   
        # self.visit(node.target, loop_frame)
        
        # self.write(extended_loop and ', l_loop in LoopContext(' or ' in ')

        # if we have an extened loop and a node test, we filter in the
        # "outer frame".
        # self.visit(node.iter, loop_frame)

        if node.recursive:
            self.write(', recurse=loop_render_func):')
        else:
            if extended_loop:
                self.writeline('var l_loop;')

            var_ref = self.temporary_identifier()
            self.writeline('var %s = '%var_ref)
            self.visit(node.iter, loop_frame);
            self.write(';')
            var_i = self.temporary_identifier()
            var_len = self.temporary_identifier()
            self.writeline('for (var %(i)s= 0, %(len)s = %(ref)s.length; %(i)s<%(len)s; %(i)s++) '%dict(i=var_i,len=var_len, ref=var_ref), node)

            #self.write(extended_loop and ')) {' or ') {')

        self.indent()
        # tests in not extended loops become a continue
        if node.test is not None:
            self.writeline('if (!(')
            self.visit(node.test, loop_frame)
            self.write(')) ')
            self.indent()
            self.writeline('continue;')
            self.outdent()

        if len(loop_vars)>1:
            self.writeline('%s;'%', '.join(['l_%s = %s[%d]'%(l,var_ref,i) for i,l in enumerate(loop_vars)]))
        else:
            self.writeline('l_%s = %s[%s];'%(loop_vars[0],var_ref,var_i))
        
        if extended_loop:
            self.writeline('l_loop = Jinja2.utils.loop(%s,%s);'%(var_i,var_len))
        self.blockvisit(node.body, loop_frame)
        if node.else_:
            self.writeline('%s = 0;' % iteration_indicator)
        self.outdent()
        if node.else_:
            self.writeline('if (%s) ' % iteration_indicator)
            self.indent()
            self.blockvisit(node.else_, loop_frame)
            self.outdent()
        # reset the aliases if there are any.
        if not node.recursive:
            self.pop_scope(aliases, loop_frame)

        # if the node was recursive we have to return the buffer contents
        # and start the iteration code
        if node.recursive:
            self.return_buffer_contents(loop_frame)
            self.outdent()
            self.start_write(frame, node)
            self.write('loop(')
            self.visit(node.iter, frame)
            self.write(', loop)')
            self.end_write(frame)

    def visit_If(self, node, frame):
        if_frame = frame.soft()
        self.writeline('if (', node)
        self.visit(node.test, if_frame)
        self.write(') ')
        self.indent()
        self.blockvisit(node.body, if_frame)
        self.outdent()
        if node.else_:
            self.writeline('else ')
            self.indent()
            self.blockvisit(node.else_, if_frame)
            self.outdent()

    def visit_Macro(self, node, frame):
        defaults = self.get_defaults(node)
        macro_frame = self.macro_body(node, frame, defaults=defaults)
        self.macro_def(node, macro_frame, defaults=defaults)
        if frame.toplevel:
            self.writeline('context.vars[%r] = l_%s;' % (node.name,node.name))
            if not node.name.startswith('_'):
                self.writeline('context.exported_vars.add(%r);' % node.name)
        frame.assigned_names.add(node.name)

    def visit_CallBlock(self, node, frame):
        children = node.iter_child_nodes(exclude=('call',))
        call_frame = self.macro_body(node, frame, children)
        self.writeline('var caller = ')
        self.macro_def(node, call_frame)
        self.start_write(frame, node)
        self.visit_Call(node.call, call_frame, forward_caller=True)
        self.end_write(frame)
        self.write(';')

    def visit_FilterBlock(self, node, frame):
        filter_frame = frame.inner()
        filter_frame.inspect(node.iter_child_nodes())
        aliases = self.push_scope(filter_frame)
        self.pull_locals(filter_frame)
        self.buffer(filter_frame)
        self.blockvisit(node.body, filter_frame)
        self.start_write(frame, node)
        self.visit_Filter(node.filter, filter_frame)
        self.end_write(frame)
        self.pop_scope(aliases, filter_frame)

    def visit_ExprStmt(self, node, frame):
        self.newline(node)
        self.visit(node.node, frame)

    def visit_Output(self, node, frame):
        # if we have a known extends statement, we don't output anything
        # if we are in a require_output_check section
        if self.has_known_extends and frame.require_output_check:
            return

        if self.environment.finalize:
            finalize = lambda x: unicode(self.environment.finalize(x))
        else:
            finalize = unicode

        # if we are inside a frame that requires output checking, we do so
        outdent_later = False
        if frame.require_output_check:
            self.writeline('if (!parent_template) ')
            self.indent()
            outdent_later = True

        # try to evaluate as many chunks as possible into a static
        # string at compile time.
        body = []
        for child in node.nodes:
            try:
                const = child.as_const(frame.eval_ctx)
            except nodes.Impossible:
                body.append(child)
                continue
            # the frame can't be volatile here, becaus otherwise the
            # as_const() function would raise an Impossible exception
            # at that point.
            try:
                if frame.eval_ctx.autoescape:
                    if hasattr(const, '__html__'):
                        const = const.__html__()
                    else:
                        const = escape(const)
                const = finalize(const)
            except Exception:
                # if something goes wrong here we evaluate the node
                # at runtime for easier debugging
                body.append(child)
                continue
            if body and isinstance(body[-1], list):
                body[-1].append(const)
            else:
                body.append([const])

        # if we have less than 3 nodes or a buffer we yield or extend/append
        if len(body) < 3 or frame.buffer is not None:
            if frame.buffer is not None:
                pass
                # for one item we append, for more we extend
                # if len(body) == 1:
                #     self.writeline('%s.push(' % frame.buffer)
                # else:
                #     pass
            for item in body:
                if isinstance(item, list):
                    val = JSVar(concat(item))
                    if frame.buffer is None:
                        self.writeline('buf += %r;'% val)
                    else:
                        self.writeline('%s += %r;'%(frame.buffer,val))
                else:
                    if frame.buffer is None:
                        self.writeline('buf += ', item)
                    else:
                        self.writeline('%s += ('%frame.buffer, item)
                    close = 1
                    if frame.eval_ctx.volatile:
                        self.write('(context.eval_ctx.autoescape and'
                                   ' escape or Jinja2.utils.to_string)(')
                    elif frame.eval_ctx.autoescape:
                        self.write('escape(')
                    else:
                        self.write('Jinja2.utils.to_string(')
                    if self.environment.finalize is not None:
                        self.write('Jinja2.finalize(')
                        close += 1
                    self.visit(item, frame)
                    self.write(')' * close)
                    self.write('')
                    if frame.buffer is not None:
                        self.write(');')

        # otherwise we create a format string as this is faster in that case
        else:
            idx = -1
            for argument in body:
                self.writeline('buf += ')
                if isinstance(argument, list):
                    self.write("%r;"%JSVar(concat(argument)))
                    continue
                close = 0
                if frame.eval_ctx.volatile:
                    self.write('(context.eval_ctx.autoescape and'
                               ' escape or String)(')
                    close += 1
                elif frame.eval_ctx.autoescape:
                    self.write('escape(')
                    close += 1
                if self.environment.finalize is not None:
                    self.write('Jinja2.finalize(')
                    close += 1
                self.visit(argument, frame)
                self.write(')' * close )
                self.write(';')

        if outdent_later:
            self.outdent()

    def visit_Assign(self, node, frame):
        self.newline(node)
        # toplevel assignments however go into the local namespace and
        # the current template's context.  We create a copy of the frame
        # here and add a set so that the Name visitor can add the assigned
        # names here.
        if frame.toplevel:
            assignment_frame = frame.copy()
            assignment_frame.toplevel_assignments = set()
        else:
            assignment_frame = frame
        self.write('var ')
        self.visit(node.target, assignment_frame)
        self.write(' = ')
        self.visit(node.node, frame)
        self.write(';')
        # make sure toplevel assignments are added to the context.
        if frame.toplevel:
            public_names = [x for x in assignment_frame.toplevel_assignments
                            if not x.startswith('_')]
            if len(assignment_frame.toplevel_assignments) == 1:
                name = next(iter(assignment_frame.toplevel_assignments))
                self.writeline('context.vars[%r] = l_%s;' % (name, name))
            else:
                self.writeline('context.vars.update({')
                for idx, name in enumerate(assignment_frame.toplevel_assignments):
                    if idx:
                        self.write(', ')
                    self.write('%r: l_%s' % (name, name))
                self.write('})')
            if public_names:
                if len(public_names) == 1:
                    self.writeline('context.exported_vars.add(%r);' %
                                   public_names[0])
                else:
                    self.writeline('context.exported_vars.update((%s));' %
                                   ', '.join(map(lambda x:repr(JSVar(x)), public_names)))

    # -- Expression Visitors

    def visit_Name(self, node, frame):
        if node.ctx == 'store' and frame.toplevel:
            frame.toplevel_assignments.add(node.name)
        self.write('l_%s'%node.name)
        frame.assigned_names.add(node.name)

    def visit_Const(self, node, frame):
        val = node.value
        self.write(repr(JSVar(val)))
        # if isinstance(val, float):
        #     self.write(str(val))
        # else:
        #     self.write(repr(val))

    def visit_TemplateData(self, node, frame):
        try:
            self.write(repr(node.as_const(frame.eval_ctx)))
        except nodes.Impossible:
            self.write('(context.eval_ctx.autoescape and escape or identity)(%r)'
                       % node.data)

    def visit_Tuple(self, node, frame):
        self.write('[')
        idx = -1
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item, frame)
        self.write(']')

    def visit_List(self, node, frame):
        self.write('[')
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item, frame)
        self.write(']')

    def visit_Dict(self, node, frame):
        self.write('{')
        for idx, item in enumerate(node.items):
            if idx:
                self.write(', ')
            self.visit(item.key, frame)
            self.write(': ')
            self.visit(item.value, frame)
        self.write('}')

    def binop(operator, interceptable=True):
        def visitor(self, node, frame):
            if self.environment.sandboxed and \
               operator in self.environment.intercepted_binops:
                self.write('Jinja2.call_binop(context, %r, ' % operator)
                self.visit(node.left, frame)
                self.write(', ')
                self.visit(node.right, frame)
            else:
                self.write('(')
                self.visit(node.left, frame)
                self.write(' %s ' % operator)
                self.visit(node.right, frame)
            self.write(')')
        return visitor

    def uaop(operator, interceptable=True):
        def visitor(self, node, frame):
            if self.environment.sandboxed and \
               operator in self.environment.intercepted_unops:
                self.write('Jinja2.call_unop(context, %r, ' % operator)
                self.visit(node.node, frame)
            else:
                self.write('(' + operator)
                self.visit(node.node, frame)
            self.write(')')
        return visitor

    visit_Add = binop('+')
    visit_Sub = binop('-')
    visit_Mul = binop('*')
    visit_Div = binop('/')
    visit_FloorDiv = binop('//')
    visit_Pow = binop('**')
    visit_Mod = binop('%')
    visit_And = binop('&&', interceptable=False)
    visit_Or = binop('||', interceptable=False)
    visit_Pos = uaop('+')
    visit_Neg = uaop('-')
    visit_Not = uaop('! ', interceptable=False)
    del binop, uaop

    def visit_Concat(self, node, frame):
        if frame.eval_ctx.volatile:
            func_name = '(context.eval_ctx.volatile and' \
                        ' markup_join or unicode_join)'
        elif frame.eval_ctx.autoescape:
            func_name = 'markup_join'
        else:
            func_name = 'unicode_join'
        self.write('%s((' % func_name)
        for arg in node.nodes:
            self.visit(arg, frame)
            self.write(', ')
        self.write('))')

    def visit_Compare(self, node, frame):
        self.visit(node.expr, frame)
        for op in node.ops:
            self.visit(op, frame)

    def visit_Operand(self, node, frame):
        self.write(' %s ' % operators[node.op])
        self.visit(node.expr, frame)

    def visit_Getattr(self, node, frame):
        self.visit(node.node, frame)
        self.write('[%r]'%node.attr)
        # self.write('environment.getattr(')
        # self.visit(node.node, frame)
        # self.write(', %r)' % node.attr)

    def visit_Getitem(self, node, frame):
        # slices bypass the environment getitem method.
        # if isinstance(node.arg, nodes.Slice):
        self.visit(node.node, frame)
        self.write('[')
        self.visit(node.arg, frame)
        self.write(']')
        # else:
        #     self.write('Jinja2.getitem(')
        #     self.visit(node.node, frame)
        #     self.write(', ')
        #     self.visit(node.arg, frame)
        #     self.write(')')

    def visit_Slice(self, node, frame):
        if node.start is not None:
            self.visit(node.start, frame)
        self.write(':')
        if node.stop is not None:
            self.visit(node.stop, frame)
        if node.step is not None:
            self.write(':')
            self.visit(node.step, frame)

    def visit_Filter(self, node, frame):
        self.write('context.callfilter(%s, ['%self.filters[node.name])
        func = self.environment.filters.get(node.name)
        if func is None:
            self.fail('no filter named %r' % node.name, node.lineno)
        if getattr(func, 'contextfilter', False):
            node.args.prepend('context')
            self.write('context, ')
        elif getattr(func, 'evalcontextfilter', False):
            self.write('context.eval_ctx, ')
        elif getattr(func, 'environmentfilter', False):
            self.write('Jinja2, ')

        # if the filter node is None we are inside a filter block
        # and want to write to the current buffer
        if node.node is not None:
            self.visit(node.node, frame)
        elif frame.eval_ctx.volatile:
            self.write('(context.eval_ctx.autoescape and'
                       ' escape(%s) or %s)' %
                       (frame.buffer, frame.buffer))
        elif frame.eval_ctx.autoescape:
            self.write('escape(%s)' % frame.buffer)
        else:
            self.write(frame.buffer)
        self.write(']')
        self.signature(node, frame)
        self.write(')')

    def visit_Test(self, node, frame):
        self.write(self.tests[node.name] + '(')
        if node.name not in self.environment.tests:
            self.fail('no test named %r' % node.name, node.lineno)
        self.visit(node.node, frame)
        self.signature(node, frame)
        self.write(')')

    def visit_CondExpr(self, node, frame):
        def write_expr2():
            if node.expr2 is not None:
                return self.visit(node.expr2, frame)
            self.write('Jinja2.undefined(%r)' % ('the inline if-'
                       'expression on %s evaluated to false and '
                       'no else section was defined.' % self.position(node)))

        if not have_condexpr:
            self.write('(')
            self.visit(node.test, frame)
            self.write(') && (')
            self.visit(node.expr1, frame)
            self.write(',) || (')
            write_expr2()
            self.write(')')
        else:
            self.write('((')
            self.visit(node.test, frame)
            self.write(')?')
            self.visit(node.expr1, frame)
            self.write(':')
            write_expr2()
            self.write(')')

    def visit_Call(self, node, frame, forward_caller=False):
        if self.environment.sandboxed:
            self.write('Jinja2.call(context, ')
        else:
            self.write('context.call(')
        self.visit(node.node, frame)
        extra_kwargs = forward_caller and {'caller': 'caller'} or None
        self.signature(node, frame, extra_kwargs)
        self.write(')')

    def visit_Keyword(self, node, frame):
        # self.write(node.key + '=')
        self.write('\'%s\':'%node.key)
        self.visit(node.value, frame)

    # -- Unused nodes for extensions

    def visit_MarkSafe(self, node, frame):
        self.write('escape(')
        self.visit(node.expr, frame)
        self.write(')')

    def visit_MarkSafeIfAutoescape(self, node, frame):
        self.write('(context.eval_ctx.autoescape and Markup or identity)(')
        self.visit(node.expr, frame)
        self.write(')')

    def visit_EnvironmentAttribute(self, node, frame):
        self.write('Jinja2.' + node.name)

    def visit_ExtensionAttribute(self, node, frame):
        self.write('Jinja2.extensions[%r].%s' % (node.identifier, node.name))

    def visit_ImportedName(self, node, frame):
        self.write(self.import_aliases[node.importname])

    def visit_InternalName(self, node, frame):
        self.write(node.name)

    def visit_ContextReference(self, node, frame):
        self.write('context')

    def visit_Continue(self, node, frame):
        self.writeline('continue;', node)

    def visit_Break(self, node, frame):
        self.writeline('break;', node)

    def visit_Scope(self, node, frame):
        scope_frame = frame.inner()
        scope_frame.inspect(node.iter_child_nodes())
        aliases = self.push_scope(scope_frame)
        self.pull_locals(scope_frame)
        self.blockvisit(node.body, scope_frame)
        self.pop_scope(aliases, scope_frame)

    def visit_EvalContextModifier(self, node, frame):
        for keyword in node.options:
            self.writeline('context.eval_ctx.%s = ' % keyword.key)
            self.visit(keyword.value, frame)
            try:
                val = keyword.value.as_const(frame.eval_ctx)
            except nodes.Impossible:
                frame.eval_ctx.volatile = True
            else:
                setattr(frame.eval_ctx, keyword.key, val)

    def visit_ScopedEvalContextModifier(self, node, frame):
        old_ctx_name = self.temporary_identifier()
        safed_ctx = frame.eval_ctx.save()
        self.writeline('%s = context.eval_ctx.save()' % old_ctx_name)
        self.visit_EvalContextModifier(node, frame)
        for child in node.body:
            self.visit(child, frame)
        frame.eval_ctx.revert(safed_ctx)
        self.writeline('context.eval_ctx.revert(%s)' % old_ctx_name)
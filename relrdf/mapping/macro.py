from relrdf import error
from relrdf.expression import nodes


class Environment(dict):
    """A variable environment for expression macro evaluation.

    An environment associates variable names with values
    (expressions). It points to an outer environment (possibly `None`)
    which may contain further variable bindings."""

    __slots__ = ('outer',)

    def __init__(self, outer=None):
        super(Environment, self).__init__()

        self.outer = outer

    def get(self, varName):
        """Return the value associated to variable `varName`.

        If the variable is not found in the current enviroment, the
        outer environment will be recursively searched for its
        value. This method always returns a copy of the expression
        referenced by the environment."""

        try:
            return self[varName].copy()
        except KeyError:
            if self.outer is not None:
                return self.outer.get(varName)
            else:
                raise error.MacroError(_("Parameter '%s' not found")
                                       % varName)

    def set(self, varName, value):
        assert(isinstance(value, nodes.ExpressionNode))
        self[varName] = value


class MacroClosure(nodes.ExpressionNode):
    """A node representing a macro expansion text.

    A macro closure represents the expansion text of a macro. The node
    contains a list of formal parameters and has a single
    subexpression, which corresponds to its expansion and which may
    contain `MacroVar` nodes. The node also points to a variable
    environment that reflects the state of the macro's lexical scope
    at definition time (None if the scope is empty or undefined).

    Closures can be expanded into full expressions by replacing the
    parameter references by their values (see the `expand` method.)"""

    __slots__ = ('params',
                 'env',)

    def __init__(self, params, env, subexpr):
        super(MacroClosure, self).__init__(subexpr)

        self.params = params
        self.env = env

    def attributesRepr(self):
        return repr(self.params)

    def prettyPrintAttributes(self, stream, indentLevel):
        stream.write(' [%s]' % ', '.join(self.params))

    def expand(self, *args):
        """Expand the macro in its context and with the given
        arguments.

        The macro's formal parameters will be replaced by the values
        given by `args` (values are copied on replacement.)
        Additionally, all parameter references found in the
        expression, that do not correspond to a parameter will be
        searched for in the macro's environment, if it is not `None`.

        The macro subexpression is copied on expansion and returned."""

        if len(self.params) != len(args):
            raise error.MacroError(_("Invalid argument count"))

        # Create the expansion environment using the arguments. The
        # closure environment is used as outer environment.
        env = Environment(self.env)
        for param, arg in zip(self.params, args):
            env.set(param, arg)

        return self._expand(self[0].copy(), env)

    def _expand(self, expr, env):
        if isinstance(expr, MacroVar):
            # Look up the macro variable.
            return env.get(expr.name)
        elif isinstance(expr, MacroClosure):
            # Just set the closure environment and don't recur.
            assert expr.env is None
            expr.env = env
            return expr
        elif isinstance(expr, MacroCall):
            # Expand the arguments before passing them to the
            # macro.
            for i, subexpr in enumerate(expr):
                expr[i] = self._expand(subexpr, env)

            # Expand the macro and return the result in place of
            # its invocation.
            return expr.closure.expand(*expr)
        else:
            for i, subexpr in enumerate(expr):
                expr[i] = self._expand(subexpr, env)
            return expr

    def expandFromValues(self, *args):
        """A wrapper for the `expand` method, that converts python
        value arguments into expressions."""

        args = list(args)
        for i, arg in enumerate(args):
            if not isinstance(arg, nodes.ExpressionNode):
                args[i] = nodes.Literal(arg)

        return self.expand(*args)

    def argsFromKeywords(self, keywords, objName=_('<unknown>')):
        """Return an argument array for this macro based on the given
        keywords.

        Matching is done a way similar to that used by Python to match
        keyword parameters to arguments. `objName` is used to report
        parameter matching errors."""

        if len(keywords) != len(self.params):
            raise TypeError(_("'%s' takes exactly %d arguments (%d given)") %
                            (objName, len(self.params), len(keywords)))

        args = [None] * len(self.params)
        for name, value in keywords.items():
            try:
                args[self.params.index(name)] = value
            except ValueError:
                raise TypeError(_("'%s' got an unexpected keyword "
                                  "argument '%s'") % (objName, name))

        return args

    def expandFromKeywords(self, **keywords):
        """A wrapper for the `expand` method, that takes parameter
        values from a set of keywords.

        This method performs value conversion if necessary."""

        return self.expandFromValues(*self.argsFromKeywords(keywords))


class MacroCall(nodes.ExpressionNode):
    """A node representing a macro invocation.

    The node points to the macro definition (a closure). The
    subexpressions are the arguments."""

    __slots__ = ('closure',)

    def __init__(self, closure, *args):
        super(MacroCall, self).__init__(*args)

        self.closure = closure


class MacroVar(nodes.Var):
    """A expression macro variable.

    The name attribute corresponds to the parameter name."""

    __slots__ = ()

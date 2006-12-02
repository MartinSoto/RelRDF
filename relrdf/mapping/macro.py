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
                return outer.get(varName)
            else:
                raise error.MacroError(_("Parameter '%s' not found")
                                       % varName)

    def set(self, varName, value):
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

    def expand(self, *args):
        """Expand the macro in its context and with the given
        arguments.

        The macro's formal parameters will be replaced by the values
        given by `args` (values are copied on replacement.)
        Additionally, all parameter references found in the
        expression, that do not correspond to a parameter will be
        searched for in the macro's environment, if it is not `None`.

        The macros subexpression is copied on expansion and returned."""

        if len(self.params) != len(args):
            raise error.MacroError(_("Invalid argument count"))

        # Create the expansion environment using the arguments. The
        # closure environment is used as outer environment.
        env = Environment(self.env)
        for param, arg in zip(self.params, args):
            env.set(param, arg)

        self._expand(self[0].copy(), env)

    def _expand(self, expr, env):
        for i, subexpr in enumerate(expr):
            if isinstance(subexpr, MacroVar):
                # Look up the macro variable.
                expr[i] = env.get(subexpr.name)
            elif isinstance(subexpr, MacroClosure):
                # Just set the closure environment and don't recur.
                assert subexpr.env is None
                subexpr.env = env
            elif isinstance(subexpr, MacroCall):
                # Expand the arguments before passing them to the
                # macro.
                args = self._expand(subexpr, env)

                # Expand the macro and return the result in place of
                # its invocation.
                return subexpr.closure.expand(*args)
            else:
                expr[i] = self._expand(subexpr, env)

        return expr


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




    

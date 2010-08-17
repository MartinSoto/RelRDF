# -*- Python -*-
#
# This file is part of RelRDF, a library for storage and
# comparison of RDF models.
#
# Copyright (c) 2005-2010 Fraunhofer-Institut fuer Experimentelles
#                         Software Engineering (IESE).
#
# RelRDF is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the
# Free Software Foundation, Inc., 59 Temple Place - Suite 330,
# Boston, MA 02111-1307, USA.

from genshi.core import Stream
from genshi.template import MarkupTemplate, Context as GenshiContext


class TemplateError(Exception):
    __slots__ = ()


def streamfunc(func):
    """Decorator to make a Genshi Stream out of a generator."""

    def wrapper(*args, **kwArgs):
        return Stream(func(*args, **kwArgs))

    return wrapper


class Context(GenshiContext):
    __slots__ = ()

    def __getattr__(self, name):
        return self[name]


class ContextObject(object):
    __slots__ = ('context')

    def __init__(self):
        self.context = None

    def contextualize(self, context):
        self.context = context


class Generator(ContextObject):
    __slots__ = ()

    arguments = None

    def displayVrt(self, **kwArgs):
        # Use a hzrToVrt component from the context to convert from
        # horizontal to vertical.
        return self.context.hzrToVrt.displayVrt(content =
                                                self.displayHrz(**kwArgs))

    def displayHrz(self, **kwArgs):
        raise TemplateError, \
            "generator '%s' cannot be displayed in horizontal mode" % \
            self.__class__.__name__


class ContextFunction(ContextObject):
    """Decorator to add a contextualize method to a function.

    When the returned wrapper is invoked, the original function is
    called with the context as a named parameter called 'context'.
    """

    __slots__ = ('func',)

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwArgs):
        kwArgs['context'] = self.context
        return self.func(*args, **kwArgs)


class Template(Generator):
    __slots__ = ()

    templateVrt = None
    templateHzr = None

    def _makeLocalContext(self):
        env = {}
        for item in self.arguments:
            try:
                env[item] = self.context[item]
            except KeyError:
                raise TemplateError, "data item '%s' not found" % item

        # Add the template itself to the context.
        env['self'] = self

        context = Context()
        context.push(env)

        return context

    @streamfunc
    def _streamWithArgs(self, kwArgs, template):
        self.context.push(kwArgs)
        for event in template.generate(self._makeLocalContext()):
            yield event
        self.context.pop()        

    def displayVrt(self, **kwArgs):
        if self.templateVrt is None:
            return super(Template, self).displayVrt(**kwArgs)

        return self._streamWithArgs(kwArgs, self.templateVrt)

    def displayHrz(self, **kwArgs):
        if self.templateHrz is None:
            return super(Template, self).displayHrz(**kwArgs)

        return self._streamWithArgs(kwArgs, self.templateHrz)


class DefaultHzrToVert(Template):
    __slots__ = ()

    arguments = ('content',)

    templateVrt = MarkupTemplate('<div>$content</div>')


class Configuration(object):
    __slots__ = ('elems',
                 'context',)

    def __init__(self, _dict=None, **kwArgs):
        self.context = Context()

        # Default elements.
        self.context.hzrToVrt = DefaultHzrToVert()
        self.context.hzrToVrt.contextualize(self.context)

        self.elems = {}
        self.update(_dict, **kwArgs)
        self.context.push(self.elems)

    def update(self, _dict=None, **kwArgs):
        if _dict is None:
            d = kwArgs
        else:
            assert len(kwArgs) == 0
            d = _dict

        # Give a context to all generator elements.
        for value in d.values():
            if isinstance(value, ContextObject):
                value.contextualize(self.context)

        # Add the elements to the context.
        self.elems.update(d)

    def get(self, name):
        return self.elems[name]

    def set(self, name, value):
        if hasattr(value, 'contextualize'):
            value.contextualize(self.context)
        self.elems[name] = value


class Renamer(Generator):
    __slots__ = ('generator',
                 'renamings',)

    def __init__(self, generator, _renamings=None, **kwArgs):
        self.generator = generator

        if _renamings is None:
            self.renamings = kwArgs
        else:
            assert len(kwArgs) == 0
            self.renamings = _renamings

    def contextualize(self, context):
        super(Renamer, self).contextualize(context)
        self.generator.contextualize(context)

    def _applyRenamings(self):
        env = {}
        for dest, orig in self.renamings.items():
            try:
                env[dest] = self.context[orig]
            except KeyError:
                raise TemplateError, \
                    "data item '%s' not found while renaming" % orig

        self.context.push(env)

    @streamfunc
    def displayVrt(self, **kwArgs):
        self._applyRenamings()
        for event in self.generator.displayVrt(**kwArgs):
            yield event
        self.context.pop()

    @streamfunc
    def displayHrz(self, **kwArgs):
        self._applyRenamings()
        for event in self.generator.displayHrz(**kwArgs):
            yield event
        self.context.pop()


if __name__ == '__main__':

    class BoldTmpl(Template):
        arguments = ('text',)

        templateHrz = MarkupTemplate('''
          <b>${text}</b>
          ''')


    class HelloTmpl(Template):
        arguments = ('name',
                     'highlight',)

        templateVrt = MarkupTemplate('''
          <h1>Hello, ${highlight.displayHrz(text=self.proc(name))}!</h1>
          ''')

        def proc(self, text):
            return text.upper()


    config = Configuration(
        main = HelloTmpl(),
        highlight = BoldTmpl(),
        name = 'world',
        hzrToVert = DefaultHzrToVert(),
        )

    print config.get('main').displayVrt(name='you').render()
    print config.get('hzrToVert').displayVrt(content='horizontal')
    print config.get('highlight').displayVrt(text='horizontal').render()

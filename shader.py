# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2015, Nicolas P. Rougier
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
import re
from snippet import *


class Shader(object):

    def __init__(self, sources=[]):
        self.sources = sources
        self.snippets = []

    def __getitem__(self, key):
        # Look for an existing snippet
        for snippet in self.snippets[::-1]:
            if snippet.name == key:
                return snippet

        # Try to create one
        return self.__call__(key)

    def __call__(self, key):
        if key in self.sources.keys():
            snippet = Snippet(code=self.sources[key], name=key)
            self.snippets.append(snippet)
            return snippet
        raise IndexError("Unknown hook (%s)" % key)


    def link(self):

        # Order snippets (topological sort according to dependencies)
        unsorted = dict([(snippet, snippet.dependencies) for snippet in self.snippets])
        sorted = []
        while unsorted:
            acyclic = False
            for node, edges in unsorted.items():
                for edge in edges:
                    if edge in unsorted:
                        break
                else:
                    acyclic = True
                    del unsorted[node]
                    sorted.append(node)
            if not acyclic:
                raise RuntimeError("A cyclic dependency occurred")
        self.snippets = sorted

        # Set unique aliases
        for i,snippet in enumerate(self.snippets):
            for constant in snippet.constants:
                constant.alias = "_sn_%d_%s" % (i+1,constant.name)
            for variable in snippet.variables:
                variable.alias = "_sn_%d_%s" % (i+1,variable.name)
            for function in snippet.functions:
                function.alias = "_sn_%d_%s" % (i+1,function.name)


        # Name variable holding computation results
        for i,snippet in enumerate(self.snippets):
            for output in snippet.outputs:
                if isinstance(output.hook, Parameter):
                    name = "_io_%d_%s" % (i+1,output.hook.name)
                elif isinstance(output.hook, Function):
                    name = "_io_%d_return" % (i+1)
                output.hook.holder = name
                for target in output.targets:
                    target.hook.holder = name


    def __str__(self):
        s = ""

        snippets = self.snippets

        # Generate code
        for snippet in snippets:
            for constant in snippet.constants:
                s += str(constant) + "\n"
            for struct in snippet.structs:
                s += str(struct) + "\n"
            for variable in snippet.variables:
                s += str(variable) + "\n"

            for function in snippet.functions:
                code = str(function) + "\n"
                for input in snippet.inputs:
                    name = input.hook.name
                    if not isinstance(input.hook, Parameter):
                        alias = input.hook.alias
                        regex = r'(?<=[^a-zA-Z0-9_])%s(?=[^a-zA-Z0-9_])' % name
                        code = re.sub(regex, alias, code)

                for input in snippet.inputs:
                    name = input.hook.name
                    alias = input.source.hook.alias
                    regex = r'(?<=[^a-zA-Z0-9_])%s(?=[^a-zA-Z0-9_])' % name
                    code = re.sub(regex, alias, code)

                for variable in snippet.variables:
                    name = variable.name
                    alias = variable.alias
                    regex = r'(?<=[^a-zA-Z0-9_])%s(?=[^a-zA-Z0-9_])' % name
                    code = re.sub(regex, alias, code)
                s += code
            s += "\n"
        s += "\n"

        # Generate main
        s += "void main() {\n"

        # Variable declarations
        for i,snippet in enumerate(snippets):
            for output in snippet.outputs:
                if isinstance(output.hook, Parameter):
                    s += "  %s _io_%d_%s;\n" % (output.type, i+1, output.hook.name)
#                if isinstance(output.hook, Function):
#                    if output.type.base not in ["", "void"]:
#                        s += "  %s _io_%d_return;\n" % (output.type, i+1)
        s += "\n"


        def call(function):
            s = "  "
            if function.type.base not in ["", "void"]:
                s += "%s %s = " % (function.type, function.holder)
            s += function.alias + "("
            parameters = function.parameters
            for i,parameter in enumerate(parameters):
                s += parameter.holder
                if i < len(parameters)-1:
                    s+= ", "
            s += ");\n"
            return s;

        for i,snippet in enumerate(self.snippets):
            for function in snippet.functions:
                function.called = False

        # Function calls
        for i,snippet in enumerate(snippets):

            for function in snippet.functions:
                for parameter in function.parameters:
                    if parameter.inout in ["inout","out"]:
                        s += call(function)
                        break

            for output in snippet.outputs:
                if isinstance(output.hook, Function):
                    need_call = False
                    for target in output.targets:
                        if isinstance(target.hook, Parameter):
                            need_call = True
                    if need_call:
                        s += call(output.hook)

            for function in snippet.functions:
                if re.search("gl_FragColor|gl_Position", function.code):
                    s += call(function)

        # for i,snippet in enumerate(self.snippets):
        #     for function in snippet.functions:
        #         s += call(function)

        s += "}\n"
        return s

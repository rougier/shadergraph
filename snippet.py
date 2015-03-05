# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2015, Nicolas P. Rougier
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
import re
from parser import *


class Input(object):
    def __init__(self, snippet, target):
        self.source = None
        self.target = target
        self.snippet = snippet

    @property
    def type(self):
        return self.target.type


class Output(object):
    def __init__(self, snippet, source):
        self.source = source
        self.target = None
        self.snippet = snippet

    @property
    def type(self):
        return self.source.type




class Snippet(object):
    """ """

    def __init__(self, code, name="anonymous"):

        self._id   = None
        self._name = name
        self._code = code
        self._build_objects()
        self._build_symbols()
        self._build_hooks()
        self._selection = None

    def _build_objects(self):
        C,S,V,P,F = parse(self._code)
        self.constants = C
        self.structs = S
        self.variables = V
        self.prototypes = P
        self.functions = F

    def _build_symbols(self):
        self.symbols = {}
        for prototype in self.prototypes:
            self.symbols[prototype.name] = prototype.name
        for function in self.functions:
            self.symbols[function.name] = function.name
        for variable in self.variables:
            self.symbols[variable.name] = variable.name

    def _build_hooks(self):
        self._inputs  = []
        for prototype in self.prototypes:
            self._inputs.append(Input(self,prototype))
        for function in self.functions:
            for parameter in function.parameters:
                if parameter.inout in ["", "in", "inout"]:
                    self._inputs.append(Input(self, parameter) )

        self._outputs = []
        for function in self.functions:
            for parameter in function.parameters:
                if parameter.inout in ["out", "inout"]:
                    self._outputs.append( Output(self, parameter) )
            if function.type.base  not in ["","void"]:
                self._outputs.append(Output(self, function))


    @property
    def name(self):
        return self._name

    @property
    def inputs(self):
        return self._inputs

    @property
    def outputs(self):
        return self._outputs

    @property
    def dependencies(self):
        deps = []
        for input in self.inputs:
            if input.source is not None:
                deps.append(input.source.snippet)
        return deps


    def __rshift__(self, other):
        self.connect(other)
        return other


    def connect(self, other):

        for output in self.outputs:
            if output.target is not None:
                continue
            for input in other.inputs:
                if input.source is not None:
                    continue
                if output.type == input.type:
                    output.target = input
                    input.source = output
                    return

        raise RuntimeError("No compatible I/O found")

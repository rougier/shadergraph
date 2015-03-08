# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2015, Nicolas P. Rougier
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
import re
from parser import *


class Input(object):
    """
    An input is an entry point in a snippet (Parameter or Prototype)
    """
    def __init__(self, snippet, hook):
        self.snippet = snippet
        self.hook    = hook
        self.source  = None

    @property
    def type(self):
        return self.hook.type


class Output(object):
    """
    An output is an exit point in a snippet (Parameter or Function)
    """
    def __init__(self, snippet, hook):
        self.snippet = snippet
        self.hook    = hook
        self.targets = []

    @property
    def type(self):
        return self.hook.type



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

    def __getitem__(self, key):
        self._selection == key
        return self


    def __rshift__(self, other):
        """
        """

        self.connect(other)
        self._selection = None
        other._selection = None
        return other


    def connect(self, other):
        """
        Try to connect this snippet (out) to the other snippet (in)
        """

        output_hook = None
        input_hook = None

        # An output hook has been selected
        if self._selection:
            for output in self.outputs:
                if output.name == self._selection:
                    output_hook = input
                    break

        # An input hook has been selected
        if other._selection:
            for input in other.inputs:
                if input.name == other._selection:
                    input_hook = input
                    break

        # Both output/input have been selected, types must match
        if input_hook and output_hook:
            if input_hook.type != output_hook.type:
                error = "Selected input and output are not compatible"
                raise RuntimeError(error)

        # Output has been selected, look for a compatible input hook
        elif output_hook:
            for input in other.inputs:
                # Input is already hooked
                if input.source is not None:
                    continue
                if input.type == output_hook.type:
                    input_hook = input
                    break
            if input_hook is None:
                error = "No compatible input found"
                raise RuntimeError(error)


        # Input has been selected, look for a compatible output hook
        elif input_hook:
            # First pass, we look for a non hooked compatible input
            for output in self.outputs:
                if output.targets:
                    continue
                elif output.type == input_hook.type:
                    output_hook = output
                    break

            # Second pass, we look for a compatible input
            if output_hook is None:
                for output in self.outputs[::-1]:
                    if output.type == input_hook.type:
                        output_hook = output
                        break

            if output_hook is None:
                error = "No compatible output found"
                raise RuntimeError(error)

        # Nothing has been selected, look for first free matching output/input
        else:
            found = False

            # First pass, we look for a non hooked compatible input
            for output in self.outputs:
                if found: break
                if output.targets: continue
                for input in other.inputs:
                    if found: break
                    if input.source is not None: continue
                    if output.type == input.type:
                        output_hook = output
                        input_hook = input
                        found = True

            # Second pass, we look for a compatible input
            if not found:
                for output in self.outputs:
                    if found: break
                    for input in other.inputs:
                        if found: break
                        if input.source is not None: continue
                        if output.type == input.type:
                            output_hook = output
                            input_hook = input
                            found = True

            if not found:
                raise RuntimeError("No compatible input / output found")

        output_hook.targets.append(input_hook)
        input_hook.source = output_hook

# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2015, Nicolas P. Rougier
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
from pyparsing import *

keywords = ("attribute const uniform varying break continue do for while"
            "if else"
            "in out inout"
            "float int void bool true false"
            "lowp mediump highp precision invariant"
            "discard return"
            "mat2 mat3 mat4"
            "vec2 vec3 vec4 ivec2 ivec3 ivec4 bvec2 bvec3 bvec4 sampler2D samplerCube"
            "struct")

reserved = ("asm"
            "class union enum typedef template this packed"
            "goto switch default"
            "inline noinline volatile public static extern external"
            "interface flat long short double half fixed unsigned superp"
            "input output"
            "hvec2 hvec3 hvec4 dvec2 dvec3 dvec4 fvec2 fvec3 fvec4 sampler1D sampler3D"
            "sampler1DShadow sampler2DShadow"
            "sampler2DRect sampler3DRect sampler2DRectShadow"
            "sizeof cast"
            "namespace using")

IDENTIFIER       = Regex('[a-zA-Z_][a-zA-Z_0-9]*')
INT_DECIMAL      = Regex('([+-]?(([1-9][0-9]*)|0+))')
INT_OCTAL        = Regex('(0[0-7]*)')
INT_HEXADECIMAL  = Regex('(0[xX][0-9a-fA-F]*)')
INTEGER          = INT_HEXADECIMAL | INT_OCTAL | INT_DECIMAL
FLOAT            = Regex('[+-]?(((\d+\.\d*)|(\d*\.\d+))([eE][-+]?\d+)?)|(\d*[eE][+-]?\d+)')
LPAREN, RPAREN   = Literal("(").suppress(), Literal(")").suppress()
LBRACK, RBRACK   = Literal("[").suppress(), Literal("]").suppress()
LBRACE, RBRACE   = Literal("{").suppress(), Literal("}").suppress()
SEMICOLON, COMMA = Literal(";").suppress(), Literal(",").suppress()
EQUAL            = Literal("=").suppress()
SIZE             = INTEGER | IDENTIFIER
OPERATOR         = oneOf("+ - * / [ ] . & ^ ! { }")
STORAGE_QUALIFIER   = Regex("const|varying|uniform|attribute")
CONST_QUALIFIER     = Literal("const")
INVARIANT_QUALIFIER = Literal("invariant")
PRECISION_QUALIFIER = Regex("lowp|mediump|highp")
PARAMETER_QUALIFIER = Regex("(in|out|inout)[ \t\n]")


# Variable declarations
# ---------------------
PART        = nestedExpr() | nestedExpr('{','}') | IDENTIFIER | INTEGER | FLOAT | OPERATOR
EXPR        = delimitedList(PART, delim=Empty()).setParseAction(keepOriginalText)
VARIABLE    = (IDENTIFIER("name") + Optional(LBRACK + SIZE + RBRACK)("size")
               + Optional(EQUAL + EXPR)("value"))
VARIABLES   = delimitedList(VARIABLE.setResultsName("variables",listAllMatches=True))
DECLARATION = (STORAGE_QUALIFIER("storage") + Optional(PRECISION_QUALIFIER)("precision") +
               IDENTIFIER("type") + VARIABLES + SEMICOLON)
DECLARATION.ignore(cStyleComment)

# Function parameter
# ------------------
PARAMETER = Group(Optional(STORAGE_QUALIFIER)("storage") +
                  Optional(PRECISION_QUALIFIER)("precision") +
                  Optional(PARAMETER_QUALIFIER)("inout") +
                  IDENTIFIER("type") + Optional(IDENTIFIER("name")) +
                  Optional(LBRACK + SIZE + RBRACK)("size"))

# Function prototypes
# -------------------
FUNCTION = (Optional(STORAGE_QUALIFIER)("storage") +
            Optional(PRECISION_QUALIFIER)("precision") +
            IDENTIFIER("type") + IDENTIFIER("name") +
            LPAREN + Optional(delimitedList(PARAMETER))("parameters") + RPAREN +
            ((nestedExpr("{", "}").setParseAction(keepOriginalText)("code")) | SEMICOLON))
FUNCTION.ignore(cStyleComment)

# Struct definitions & declarations
# ---------------------------------
STRUCT = ( Literal("struct").suppress() + IDENTIFIER("type") +
           nestedExpr("{", "}").setParseAction(keepOriginalText)("content") +
           Optional(VARIABLES) + SEMICOLON)
STRUCT.ignore(cStyleComment)

# Constants
# ---------
CONSTANT = (Literal("#").suppress() + Literal("define").suppress() +
            IDENTIFIER("name") + restOfLine("value"))


class Type(object):
    def __init__(self, base=None, storage=None, precision=None, size=None):
        if isinstance(base, Type):
            other = base
            self.base = other.base
            self.size = other.size
            self.storage = other.storage
            self.precision = other.precision
        else:
            self.base = base.strip()
            self.size = size.strip()
            self.storage = storage.strip()
            self.precision = precision.strip()

    def __str__(self):
        s = ""
        if self.storage:
            s += "%s " % self.storage
        if self.precision:
            s += "%s " % self.precision
        s += "%s" % self.base
        return s

    def __eq__(self, other):
        return (self.base == other.base and
                self.size == other.size and
                self.precision == other.precision)


class Parameter(object):
    def __init__(self, type, name=None, inout="in"):
        self.type = Type(type)
        self.name = name.strip()
        self.alias = name.strip()
        self.inout = inout.strip()

    def __str__(self):
        s = ""
        if self.inout: s += "%s " % self.inout
        s += str(self.type) + " "
        if self.name:  s += "%s" % self.name
        if self.type.size: s += "[%s]" % self.size
        return s


class Variable(object):
    def __init__(self, type, name, value=None):
        self.type = Type(type)
        self.name = name.strip()
        self.alias = name.strip()
        self.value = value.strip()

    def __str__(self):
        s = str(self.type) + " " + self.alias
        if self.type.size:
            s += "[%s]" % self.type.size
        if self.value:
            s += " = %s" % self.value
        s += ";"
        return s


class Prototype(object):
    def __init__(self, type, name, parameters):
        self.type = Type(type)
        self.name = name.strip()
        self.alias = name.strip()
        self.parameters = parameters

    def __str__(self):
        s = str(self.type) + " %s (" % self.alias
        for i, parameter in enumerate(self.parameters):
            s += str(parameter)
            if i < len(self.parameters)-1:
                s+= ", "
        s += ");"
        return s


class Function(object):
    def __init__(self, type, name, parameters, code):
        self.type = Type(type)
        self.name = name.strip()
        self.alias = name.strip()
        self.parameters = parameters
        self.code = code.strip()

    def __str__(self):
        s = str(self.type) + " %s (" % self.alias
        for i, parameter in enumerate(self.parameters):
            s += str(parameter)
            if i < len(self.parameters)-1:
                s+= ", "
        s += ") "
        s += self.code
        return s


class Constant(object):
    def __init__(self, name, value):
        self.name = name.strip()
        self.alias = name.strip()
        self.value = value.strip()

    def __str__(self):
        s = "#define %s %s" % (self.alias, self.value)
        return s

    def __eq__(self, other):
        return self.value == other.value


class Struct(object):
    def __init__(self, name, content):
        self.name = name.strip()
        self.content = content.strip()

    def __str__(self):
        s = "struct %s %s;" % (self.name, self.content)
        return s



def parse(code):
    """ Parse a GLSL source code into an abstract syntax list """

    constants = []
    structs   = []
    variables = []
    prototypes= []
    functions = []


    # Constants
    for (token, start, end) in CONSTANT.scanString(code):
        C = Constant(name  = token.name,
                     value = token.value)
        constants.append(C)


    # Variables
    for (token, start, end) in DECLARATION.scanString(code):
        for variable in token.variables:
            size = '' if not variable.size else variable.size[0]
            value = '' if not variable.value else variable.value[0]
            V = Variable(Type(base      = token.type,
                              storage   = token.storage,
                              precision = token.precision,
                              size      = size),
                         name = variable.name,
                         value = value)
            variables.append(V)


    # Struct definitions & declarations
    for (token, start, end) in STRUCT.scanString(code):
        S = Struct(name    = token.type,
                   content = token.content[0])
        structs.append(S)
        for variable in token.variables:
            size = '' if not variable.size else variable.size[0]
            value = '' if not variable.value else variable.value[0]
            V = Variable(Type(base = token.type,
                              size = size),
                         name = variable.name,
                         value = value)
            variables.append(V)

    # Functions prototype and definitions
    for (token, start, end) in FUNCTION.scanString(code):
        parameters = []
        for parameter in token.parameters:
            size = '' if not parameter.size else parameter.size[0]
            P = Parameter(type = Type(base      = parameter.type,
                                      storage   = parameter.storage,
                                      precision = parameter.precision,
                                      size      = parameter.size),
                          name = parameter.name,
                          inout = parameter.inout)
            parameters.append(P)
        T = Type(base      = token.type,
                 storage   = token.storage,
                 precision = token.precision,
                 size      = token.size)
        if token.code:
            F = Function( type = T,
                          name = token.name,
                          parameters = parameters,
                          code = token.code[0])
            functions.append(F)
            for parameter in parameters:
                parameter.function = F
        else:
            P = Prototype(type = T,
                          name = token.name,
                          parameters = parameters)
            prototypes.append(P)
            for parameter in parameters:
                parameter.function = None

    return constants, structs, variables, prototypes, functions

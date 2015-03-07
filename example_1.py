# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2015, Nicolas P. Rougier
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
from shader import Shader


get_colors = """
uniform vec4 diffuse_color;
void get_colors(out vec4 color1, out vec4 color2)
{
    color1 = diffuse_color;
    color2 = diffuse_color.zyxw;
} """

apply_filter = """
uniform float intensity;
vec4 apply_filter(vec4 ramp)
{
    return mix(ramp, ramp * (1.0 - ramp) * 2.0, intensity);
} """

combine = """
vec4 combine_colors(vec4 a, vec4 b)
{
    return a + b;
}
"""

set_color = """
void set_color(vec4 color)
{
    gl_FragColor = color;
}
"""

snippets = { 'get_colors'    : get_colors,
             'apply_filter'  : apply_filter,
             'combine'       : combine,
             'set_color'     : set_color }

# ("snippet") -> Explicitly creates snippet
# ["snippet"] -> Reuse snippet or create a new one if not found
# ["snippet"]["hook"] -> Select "hook" (input or output)
shader = Shader(snippets)
shader("get_colors") >> shader("apply_filter") >> shader("combine") >> shader("set_color")
shader["get_colors"] >> shader("apply_filter") >> shader["combine"]
shader.link()

print shader

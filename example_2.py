# -*- coding: utf-8 -*-
# -----------------------------------------------------------------------------
# Copyright (c) 2015, Nicolas P. Rougier
# Distributed under the (new) BSD License. See LICENSE.txt for more info.
# -----------------------------------------------------------------------------
from shader import Shader


get_color = """
vec3 get_color()
{
  return vec3(0.2, 0.3, 0.4);
} """

get_color_sum = """
vec3 get_color1();
vec3 get_color2();
vec3 get_color_sum() {
  return get_color1() + get_color2();
}
"""

set_color = """
vec3 get_color();
void main() {
  gl_FragColor = vec4(get_color(), 1.0);
}
"""

snippets = { 'get_color'    : get_color,
             'get_color_sum': get_color_sum,
             'set_color'    : set_color }

shader = Shader(snippets)
shader("get_color") >> shader("get_color_sum") >> shader("set_color")
shader("get_color") >> shader["get_color_sum"]
shader.link()

print shader

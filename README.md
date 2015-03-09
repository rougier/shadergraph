
# Shadergraph

This is a python port of [shadergraph] functional GLSL linker.

# Snippet

A snippet is a small piece of vanilla GLSL code having one or more functions.
As such, it provides inputs (parameters and prototypes) and outputs (parameters
and function). For example, the following function:

    vec4 opaque(vec3 color)
    {
        return vec4(color,1.0);
    }

provides one input (`vec3`) and one output (`vec4`), while the following:

    void black(out vec3 color)
    {
        color = vec3(0.0);
    }

offers only one output (`vec3`).


# Connecting snippets



[shadergraph]: https://github.com/unconed/shadergraph

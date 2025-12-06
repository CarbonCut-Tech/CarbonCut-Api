from py_mini_racer import py_mini_racer
import os

def render_ejs_template(template_path, context):
    with open(template_path, "r") as f:
        template = f.read()
    ctx = py_mini_racer.MiniRacer()
    ejs_lib_path = os.path.join(os.path.dirname(__file__), "ejs.min.js")
    with open(ejs_lib_path, "r") as f:
        ejs_lib = f.read()
    ctx.eval(ejs_lib)
    ctx.eval(f"var template = `{template}`;")
    ctx.eval(f"var context = {context};")
    return ctx.eval("ejs.render(template, context);")
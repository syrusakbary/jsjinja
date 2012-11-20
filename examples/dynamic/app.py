from flask import Flask, render_template, url_for, Response, redirect
import json

app = Flask(__name__)

app.jinja_env.add_extension('jinja2js.ext.Jinja2JsExtension')
app.jinja_env.autoescape = False
app.debug = True

template_context = {
    'sites': [
        {
            'name': 'Google',
            'url': 'http://google.com/'
        },
        {
            'name': 'Youtube',
            'url': 'http://youtube.com/'
        },
        {
            'name': 'Facebook',
            'url': 'http://facebook.com/'
        },
        {
            'name': 'Syrus Akbary',
            'url': 'http://syrusakbary.com/'
        }
    ],
}

@app.route("/")
def index():
    return redirect(url_for('render.js'))

@app.route("/js",endpoint="render.js")
def js():
    template_context_js = dict(template_context, js=True, other_url = url_for('render.python'))
    return render_template("index.html",template_context= json.dumps(template_context_js))

@app.route("/templates.js")
def js_templates():
    ret = '/* Jinja2 javascript runtime (minified) */\n'
    ret += app.jinja_env.jinja2js.lib(minified=True)
    ret += '\n/* Js compiled templates */\n'
    ret += app.jinja_env.jinja2js.generate_all()
    return Response(response=ret, status=200, mimetype="text/javascript")

@app.route("/python",endpoint="render.python")
def python():
    template_context_normal = dict(template_context, js=False, other_url = url_for('render.js'))
    return render_template("layout.html", **template_context_normal)

if __name__ == "__main__":
    app.run()

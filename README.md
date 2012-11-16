Jinja2Js: Use your Jinja2 Templates in Js
=========================================

Jinja2Js lets you use your [Jinja2](http://jinja.pocoo.org/) templates
in Javascript. It **compile the Jinja2 templates to Javascript with 
no restrictions**. The output can be included via script tags or can be added
through the `{% jinja2js %}` tag to the templates.

# Nutshell

Here a small example of a Jinja template:

{% extends 'base.html' %}
{% block title %}Memberlist{% endblock %}
{% block content %}
  <ul>
  {% for user in users %}
    <li><a href="{{ user.url }}">{{ user.username }}</a></li>
  {% endfor %}
  </ul>
{% endblock %}

And here is the javascript compiled template:


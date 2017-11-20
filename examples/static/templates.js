(function() {
  __hasProp = {}.hasOwnProperty;
  __extends = function(a, b) {
    function e() {
      this.constructor = a;
    }
    for (var c in b) __hasProp.call(b, c) && (a[c] = b[c]);
    e.prototype = b.prototype;
    a.prototype = new e();
    a.__super__ = b.prototype;
    return a;
  };
  var g,
    c,
    k,
    l,
    m =
      [].indexOf ||
      function(a) {
        for (var b = 0, e = this.length; b < e; b++)
          if (b in this && this[b] === a) return b;
        return -1;
      };
  l = "undefined" !== typeof exports && null !== exports ? exports : this;
  k = function(a, b, e, c, f) {
    e = e || {};
    return new g(c ? e : f, a, b);
  };
  var j = function() {};
  j.prototype.add = function(a) {
    return (this[a] = !0);
  };
  j.prototype.remove = function(a) {
    return delete this[a];
  };
  var h = function() {
    var a, b;
    this.blocks = {};
    for (b in this)
      0 === b.indexOf("block_") &&
        ((a = b.slice(6)),
        (this.blocks[a] = this[b]),
        (this.blocks[a].__append_context__ = !0));
  };
  h.prototype.root = function() {};
  h.prototype.render = function(a) {
    var b;
    b = new g(null, null, this.blocks);
    b.vars = a;
    return this.root(b);
  };
  h.prototype.module = function() {
    var a, b, e;
    a = new g();
    this.root(a);
    e = {};
    for (b in a.exported_vars) e[b] = a.vars[b];
    return e;
  };
  h.prototype.new_context = function(a, b, e) {
    return k(this.name, this.blocks, a, b, this.globals, e);
  };
  var i = function(a, b, e) {
    var c;
    this.parent = a;
    this.vars = {};
    this.blocks = {};
    for (c in e) this.blocks[c] = [e[c]];
    this.exported_vars = new j();
  };
  i.prototype["super"] = function(a, b) {
    var c, d;
    c = this.blocks[a];
    d = c.indexOf(b) + 1;
    return c[d];
  };
  i.prototype.resolve = function(a) {
    var b;
    return (
      this.vars[a] ||
      (null != (b = this.parent) ? b.resolve(a) : void 0) ||
      c.globals[a]
    );
  };
  i.prototype.call = function(a, b, c) {
    var d, f, g;
    if (a) {
      f = !a.__args__ ? b : [];
      a.__append_context__ && f.push(this);
      a.__append_args__ && f.push(b);
      a.__append_kwargs__ && f.push(c);
      for (d in a.__args__)
        f.push(c[null != (g = a.__args__) ? g[d] : void 0] || b.pop());
      return a.apply(a.constructor || null, f);
    }
  };
  i.prototype.callfilter = function(a, b, c, d) {
    var f;
    if (a) {
      for (f in a.__args__) b.push(d[a.__args__[f]] || c.pop());
      return a.apply(null, b);
    }
  };
  g = i;
  c = {
    templates: {},
    filters: {},
    globals: {},
    tests: {},
    registerGlobal: function(a, b) {
      return (this.globals[a] = b);
    },
    registerFilter: function(a, b) {
      return (this.filters[a] = b);
    },
    registerTest: function(a, b) {
      return (this.tests[a] = b);
    },
    getFilter: function(a) {
      return this.filters[a];
    },
    registerTemplate: function(a, b) {
      return (this.templates[a] = b);
    },
    getTemplate: function(a) {
      return new this.templates[a]();
    },
    utils: {
      to_string: function(a) {
        return a ? String(a) : "";
      },
      missing: void 0,
      loop: function(a, b) {
        return {
          first: 0 === a,
          last: a === b - 1,
          index: a + 1,
          index0: a,
          revindex: b - a,
          revindex0: b - a - 1,
          length: b,
          cycle: function() {
            return arguments[a % arguments.length];
          }
        };
      }
    },
    extends: __extends,
    Template: h,
    Context: g
  };
  l.Jinja2 = c;
  c.registerGlobal("range", function() {
    var a, b, c, d;
    d = b = c = void 0;
    a = [];
    switch (arguments.length) {
      case 1:
        c = 0;
        b = Math.floor(arguments[0]) - 1;
        d = 1;
        break;
      case 2:
      case 3:
        (c = Math.floor(arguments[0])),
          (b = Math.floor(arguments[1]) - 1),
          (d = arguments[2]),
          "undefined" === typeof d && (d = 1),
          (d = Math.floor(d));
    }
    if (0 < d) for (; c <= b; ) a.push(c), (c += d);
    else if (0 > d && ((d = -d), c > b))
      for (; c > b + 1; ) a.push(c), (c -= d);
    return a;
  });
  c.registerGlobal(
    "dict",
    (function() {
      var a;
      a = function(a) {
        return a;
      };
      a.__append_kwargs__ = !0;
      return a;
    })()
  );
  c.registerGlobal("cycler", function() {
    var a;
    a = {
      items: arguments,
      reset: function() {
        return a._setPos(0);
      },
      _setPos: function(b) {
        a.pos = b;
        return (a.current = a.items[b]);
      },
      next: function() {
        var b;
        b = a.current;
        a._setPos((a.pos + 1) % a.items.length);
        return b;
      }
    };
    a.reset();
    return a;
  });
  c.registerGlobal("joiner", function(a) {
    var b;
    a || (a = ",");
    b = !1;
    return function() {
      if (b) return a;
      b = !0;
      return "";
    };
  });
  c.registerFilter("length", function(a) {
    return a.length;
  });
  c.registerFilter("count", function(a) {
    return a.length;
  });
  c.registerFilter("indent", function(a, b, c) {
    b || (b = 4);
    b = b ? Array(b + 1).join(" ") : "";
    return (c ? a : a.replace(/\n$/, "")).replace(/\n/g, "\n" + b);
  });
  c.registerFilter("random", function(a, b) {
    if (b) return b[Math.floor(Math.random() * b.length)];
  });
  c.registerFilter("last", function(a, b) {
    if (b) return b[b.length - 1];
  });
  c.registerFilter("first", function(a, b) {
    if (b) return b[0];
  });
  c.registerFilter("title", function(a) {
    return a.replace(/\w\S*/g, function(a) {
      return a.charAt(0).toUpperCase() + a.substr(1).toLowerCase();
    });
  });
  c.registerFilter("lower", function(a) {
    return a.toLowerCase();
  });
  c.registerFilter("upper", function(a) {
    return a.toUpperCase();
  });
  c.registerFilter("capitalize", function(a) {
    return a.charAt(0).toUpperCase() + a.slice(1);
  });
  c.registerFilter("escape", function(a) {
    return String(a)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  });
  c.registerFilter("default", function(a, b, c) {
    return (c && !a) || void 0 === a ? b : a;
  });
  c.registerFilter("truncate", function(a, b, c, d) {
    b || (b = 255);
    d || (d = "...");
    if (a.length <= b) return a;
    if (c) return a.substring(0, b);
    a = a.substring(0, maxLength + 1);
    a = a.substring(0, Math.min(a.length, a.lastIndexOf(" ")));
    return a + d;
  });
  c.registerTest("callable", function() {
    return !(!obj || !obj.constructor || !obj.call || !obj.apply);
  });
  c.registerTest("odd", function(a) {
    return 1 === a % 2;
  });
  c.registerTest("even", function(a) {
    return 0 === a % 2;
  });
  c.registerTest("divisibleby", function(a, b) {
    return 0 === a % b;
  });
  c.registerTest("defined", function(a) {
    return "undefined" !== typeof a;
  });
  c.registerTest("undefined", function(a) {
    return "undefined" === typeof a;
  });
  c.registerTest("none", function(a) {
    return null === a;
  });
  c.registerTest("lower", function(a) {
    return a === a.toLowerCase();
  });
  c.registerTest("upper", function(a) {
    return a === a.toUpperCase();
  });
  c.registerTest("string", function(a) {
    return "[object String]" === toString.call(a);
  });
  c.registerTest("mapping", function(a) {
    return a === Object(a);
  });
  c.registerTest("number", function(a) {
    return "[object Number]" === toString.call(a);
  });
  c.registerTest("sequence", function(a) {
    return "[object Array]" === toString.call(a);
  });
  c.registerTest("sameas", function(a, b) {
    return a === b;
  });
  c.registerTest("iterable", function(a) {
    return "[object Array]" === toString.call(a);
  });
  c.registerTest("escaped", function(a) {
    return 0 <= m.call(a, "__html__");
  });
}.call(this));
(function() {
  /* base.html */
  Jinja2.extends(Template, Jinja2.Template);
  Jinja2.registerTemplate("base.html", Template);
  function Template() {
    return Template.__super__.constructor.apply(this, arguments);
  }
  Template.prototype.root = function(context) {
    var buf = "";
    buf += "Site template\n";
    buf += context.blocks["content"][0](context);
    return buf;
  };
  Template.prototype.block_content = function(context) {
    var buf = "";
    buf += "\n<p>This is the main content</p>\n";
    return buf;
  };
  return Template;
})();
(function() {
  /* layout.html */
  Jinja2.extends(Template, Jinja2.Template);
  Jinja2.registerTemplate("layout.html", Template);
  function Template() {
    return Template.__super__.constructor.apply(this, arguments);
  }
  Template.prototype.root = function(context) {
    var buf = "";
    var parent_template = Jinja2.getTemplate("base.html", "layout.html");
    for (name in parent_template.blocks) {
      var parent_block = parent_template.blocks[name];
      context.blocks[name] = context.blocks[name] || [];
      context.blocks[name].push(parent_block);
    }
    buf += parent_template.root(context);
    return buf;
  };
  Template.prototype.block_content = function(context) {
    var buf = "";
    var l_super = context.super("content", Template.prototype.block_content);
    var l_sites = context.resolve("sites");
    t_1 = Jinja2.filters["count"];
    buf += "\n  ";
    buf += context.call(l_super, [], {});
    buf += "\n  <p>Total sites: ";
    buf += context.callfilter(t_1, [l_sites], [], {});
    buf += "</p>\n  <ul>\n    ";
    var l_site = undefined;
    var t_2 = l_sites;
    for (var t_3 = 0, t_4 = t_2.length; t_3 < t_4; t_3++) {
      l_site = t_2[t_3];
      buf += '\n    <li><a href="';
      buf += l_site["url"];
      buf += '">';
      buf += l_site["name"];
      buf += "</a></li>\n    ";
    }
    l_site = undefined;
    buf += "\n  </ul>\n";
    return buf;
  };
  return Template;
})();

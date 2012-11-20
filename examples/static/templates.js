(function() {
    Jinja2.extends(Template, Jinja2.Template);
    Jinja2.registerTemplate("base.html", Template);
    function Template() {return Template.__super__.constructor.apply(this, arguments);};
    Template.prototype.root = function (context) {
        var buf = "";
        buf += "Site template\n";
        buf += context.blocks['content'][0](context);
        return buf;
    }
    Template.prototype.block_content = function (context) {
        var buf = "";
        buf += "\n<p>This is the main content</p>\n";
        return buf;
    }
    return Template;
})();
(function() {
    Jinja2.extends(Template, Jinja2.Template);
    Jinja2.registerTemplate("layout.html", Template);
    function Template() {return Template.__super__.constructor.apply(this, arguments);};
    Template.prototype.root = function (context) {
        var buf = "";
        var parent_template = Jinja2.getTemplate("base.html", "layout.html");
        for (name in parent_template.blocks) {
            var parent_block = parent_template.blocks[name];
            context.blocks[name] = context.blocks[name] || [];
            context.blocks[name].push(parent_block)
        }
        buf += parent_template.root(context);
        return buf;
    }
    Template.prototype.block_content = function (context) {
        var buf = "";
        var l_super = context.super("content", Template.prototype.block_content)
        var l_sites = context.resolve("sites");
        t_1 = Jinja2.filters["count"]
        buf += '\n  ';
        buf += context.call(l_super, [], {});
        buf += '\n  <p>Total sites: ';
        buf += context.callfilter(t_1, [l_sites], [], {});
        buf += '</p>\n  <ul>\n    ';
        var l_site = undefined;
        var t_2 = l_sites;
        for (var t_3= 0, t_4 = t_2.length; t_3<t_4; t_3++) {
            l_site = t_2[t_3];
            buf += '\n    <li><a href="';
            buf += l_site['url'];
            buf += '">';
            buf += l_site['name'];
            buf += '</a></li>\n    ';
        }
        l_site = undefined;
        buf += "\n  </ul>\n";
        return buf;
    }
    return Template;
})();

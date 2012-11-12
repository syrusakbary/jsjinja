var Jinja2 = new (function(root) {

    var Set = function() {}
    Set.prototype.add = function(o) { this[o] = true; }
    Set.prototype.remove = function(o) { delete this[o]; }

    var _this = this;
    /* ECMAScript 5!! */
    if (!Object.create) {
        Object.create = function(prototype) {
            function p() {}
            p.prototype = prototype;
            return new p();
        };
    }

    __hasProp = {}.hasOwnProperty
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor(); child.__super__ = parent.prototype; return child; };

    var templates = {}
    this.register = function(template_name, template) {
        templates[template_name] = template;
        return template
    }
    this.get = function(name, parent) {
        return new templates[name](_this)
    }

    function new_context(environment, template_name, blocks, vars, shared, globals, locals) {
        vars = vars || {}
        parent = shared?vars:globals
        return new _this.Context(environment, parent, template_name, blocks)
    }
    this.Template = (function() {

        function Template(environment) {
            this.environment = environment || _this;
            this.blocks = {}
            for (var key in this) {
                // log(key.slice(6),key.indexOf('block_'))
                if (key.indexOf('block_')==0) {this.blocks[key.slice(6)] = this[key];log('____________',key.slice(6))}
            }
            log('******************************',this.blocks['base']||false)
        }
        Template.prototype.root = function() {
            return ''
        }
        Template.prototype.render = function(dict_context) {
            context = new _this.Context(this.environment, null, null, this.blocks)
            context.vars = dict_context;
            return this.root(context)
        }
        Template.prototype.module = function() {
            context = new _this.Context(this.environment)
            this.root(context)
            module = {}
            for (var key in context.exported_vars) module[key] = context.vars[key]
            return module
        }
        Template.prototype.new_context = function(vars,shared,locals) {
                return new_context(this.environment, this.name, this.blocks, vars, shared, this.globals, locals)
        }
        Template.register = function(template_name, child) {
            Jinja2.register(template_name, child);
            return __extends(child, Template);
        }
        return Template;

    })();

    this.Context = (function() {

        function Context(environment, parent, name, blocks) {
            this.environment = environment;
            this.parent = parent;
            this.vars = {}
            this.blocks = {}
            for (block_name in blocks) this.blocks[block_name] = [blocks[block_name]]
            this.exported_vars = new Set()
        }
        Context.prototype.super = function(name, current) {
            log('*****___',current||false)
            blocks = this.blocks[name]
            index = blocks.indexOf(current) + 1
            return blocks[index]
        }
        Context.prototype.resolve = function(key) {
            return this.vars[key] || (this.parent?this.parent.resolve(key):undefined);
        }
        Context.prototype.call = function (f,args,kwargs) {
            call_args = []
            for (arg in f.__args__) {
                call_args.push(kwargs[f.__args__[arg]] || args.pop())
            }
            return f.apply(null, call_args)
        }
        return Context;

    })();
    this.filters = {
        capitalize: function (str) {
            return str.charAt(0).toUpperCase() + str.slice(1);
        },
        escape: function escape(html){
          return String(html)
            .replace(/&(?!(\w+|\#\d+);)/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
        }
    }
    this.utils = {
        to_string: function(x) {
            return x?String(x):''
        },
        missing: undefined,
        loop:function(i,len) {
            return {
                first:i==0,
                last:i==(len-1),
                index:i+1,
                index0:i,
                revindex:len-i,
                revindex0:len-i-1,
                length:len
            }
        }
    }
})(this);
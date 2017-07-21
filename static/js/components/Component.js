function Component(app, meta)
{
    this.app = app;
    this.meta = meta;
    this.children = {};
    this._id = "component-" + Component.counter.toString();
    this.leaf = Component.utils.isLeaf(meta);

    Component.counter++;

    if(this.leaf) return;

    for(var key in this.meta)
    {
        if(key === "name" || key === "description" || key === "list") continue;
        this.children[key] = Component.create(app, this.meta[key]);
        this.children[key].name = Component.utils.getName(this.meta, key);
    }
}

Component.counter = 0;
Component.components = [];

Component.registerComponent =
    function(c)
    {
        Component.components.push(c);
    };

Component.use =
    function(meta)
    {
        return false;
        //return Component.utils.isLeaf(meta);
    };

Component.create =
    function(app, meta)
    {
        var match = null;
        for(var component of Component.components)
            if(component.use(meta))
                match = new component(app, meta);

        //Default on Component
        if (match === null) match = new Component(app, meta);
        return match;
    };

Component.prototype._path = null;

Component.prototype.sendUpdate =
    function(data)
    {
        this.update(data);
        for(var key in this.children)
            this.children[key].sendUpdate(data[key]);
    };

Component.prototype.update =
    function(data) {};

Component.prototype.generate =
    function()
    {
        //Placeholder for debugging: display JSON or value
        return Component.utils.isLeaf(this.meta)
            ? this.meta.value
            : JSON.stringify(this.meta);
    };

Component.prototype.sendInit =
    function(path)
    {
        if(path === undefined)
            path = "";

        this._path = path.substring(1);
        this.init();

        for(var key in this.children)
            this.children[key].sendInit(`${path}/${key}`);
    };

Component.prototype.init =
    function() {};

Component.prototype.getID =
    function()
    {
        return this._id;
    }

Component.prototype.getPath =
    function()
    {
        return this._path;
    }

Component.prototype.getName =
    function()
    {
        return this.name;
    }

//Some utility methods
Component.utils = {};

Component.utils.isLeaf =
    function(node)
    {
        for(var key in node)
            if(node[key] instanceof Object)
                return false;
        return true;
    };

Component.utils.getName =
    function(parentMeta, childName)
    {
        var name = parentMeta[childName].hasOwnProperty("name")
            ? parentMeta[childName].name
            : childName;
        return name.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
    };

Component.utils.height =
    function(component)
    {
        if(component.leaf) return 0;
        var max = 0;
        for(var key in component.children) max = Math.max(max, Component.utils.height(component.children[key]));
        return max + 1;
    }

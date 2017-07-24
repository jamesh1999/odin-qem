function Adapter(app, mount, name, meta)
{
    this.layout = new Layout(app, meta);
    this.layout.name = name;
    mount.innerHTML = this.layout.generate("main");
    this.layout.sendInit();
}

Adapter.prototype.update =
    function(data)
    {
        this.layout.sendUpdate(data);
    };

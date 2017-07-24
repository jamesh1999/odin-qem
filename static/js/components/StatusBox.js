function StatusBox(app, meta)
{
    Component.call(this, app, meta);
}

StatusBox.use =
    function(meta)
    {
        return Component.utils.isLeaf(meta)
            && (meta.type === "bool" || meta.type === "status")
            && !meta.writeable;
    };

StatusBox.prototype = new Component();

StatusBox.prototype.oldValue = null;
StatusBox.prototype.statusElem = null;

StatusBox.prototype.update =
    function(data)
    {
        if(data === this.oldValue) return;

        this.oldValue = data;
        this.statusElem.classList.remove("status-ok");
        this.statusElem.classList.remove("status-warn");

        if(data === true || data === "ok")
            this.statusElem.classList.add("status-ok");
        else if(data === "warn")
            this.statusElem.classList.add("status-warn");
    };

StatusBox.prototype.generate =
    function()
    {
        var ret = `
<div class="status" id="${this.getID()}" `;
        if(this.meta.hasOwnProperty("description"))
        {
            ret += `title="${this.meta.description}"`;
        }
        ret += `></div>`;
        return ret;
    };

StatusBox.prototype.init =
    function()
    {
        this.statusElem = document.getElementById(this.getID());
    }

Component.registerComponent(StatusBox);

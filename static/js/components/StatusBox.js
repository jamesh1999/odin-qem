function StatusBox(app, meta)
{
    Component.call(this, app, meta);
}

StatusBox.use =
    function(meta)
    {
        return Component.utils.isLeaf(meta)
            && meta.type === "bool"
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
        if(data)
            this.statusElem.classList.add("status-ok");
        else
            this.statusElem.classList.remove("status-ok");
    };

StatusBox.prototype.generate =
    function()
    {
        return `
<div class="status" id="${this.getID()}"></div>
        `;
    };

StatusBox.prototype.init =
    function()
    {
        this.statusElem = document.getElementById(this.getID());
    }

Component.registerComponent(StatusBox);

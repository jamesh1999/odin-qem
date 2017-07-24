function Label(app, meta)
{
    Component.call(this, app, meta);
}

Label.use =
    function(meta)
    {
        return Component.utils.isLeaf(meta)
            && meta.type !== "bool"
            && !meta.writeable;
    }

Label.prototype = new Component();

Label.prototype.textElem = null;
Label.prototype.oldValue = null;
Label.prototype.dp = 0;

Label.prototype.update =
    function(data)
    {
        if(data === this.oldValue) return;

        if(this.dp)
            data = data.toFixed(this.dp);

        this.oldValue = data;
        this.textElem.nodeValue = data.toString();
    };

Label.prototype.generate =
    function()
    {
        if(this.meta.hasOwnProperty("dp")) this.dp = this.meta.dp;

        var ret = `
<span id="${this.getID()}"`;
        if(this.meta.hasOwnProperty("description"))
        {
            ret += `title="${this.meta.description}"`;
        }
        ret += `>-</span>`;
        if(this.meta.hasOwnProperty("units"))
        {
            ret += `
<span>${this.meta.units}</span>`;
        } 
        return ret;
    };

Label.prototype.init =
    function()
    {
        this.textElem = document.getElementById(this.getID()).childNodes[0];
    };

Component.registerComponent(Label);

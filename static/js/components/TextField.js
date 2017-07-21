function TextField(app, meta)
{
    Component.call(this, app, meta);
}

TextField.use =
    function(meta)
    {
        return Component.utils.isLeaf(meta)
            && meta.type != "bool"
            && meta.writeable;
    };

TextField.prototype = new Component();

TextField.prototype.oldValue = null;
TextField.prototype.textElem = null;
TextField.prototype.buttonElem = null;
TextField.prototype.float = false;
TextField.prototype.dp = 0;

TextField.prototype.update =
    function(data)
    {
        if(this.dp)
            data = data.toFixed(this.dp);

        if(data === this.oldValue) return;

        this.oldValue = data;
        this.textElem.placeholder = data.toString();
    };

TextField.prototype.generate =
    function()
    {
        if(this.meta.hasOwnProperty("dp"))
            this.dp = this.meta.dp;

        if(this.meta.type === "int" || this.meta.type === "float")
            this.float = true;

        ret = `
<div class="input-group" ${this.meta.hasOwnProperty("description") ? "title=\"" + this.meta.description + "\"" : ""}>
    <input class="form-control ${this.float ? "text-right" : ""}" id="${this.getID()}-input" type="text" aria-label="Value"/>`;
        
        if(this.meta.hasOwnProperty("units"))
        {
            ret += `
    <span class="input-group-addon">${this.meta.units}</span>`;
        }
        
        ret += `
    <div class="input-group-btn">
        <button class="btn btn-default" id="${this.getID()}-button" type="button">Set</button>
    </div>
</div>
        `;

        return ret;
    };

TextField.prototype.init =
    function()
    {
        this.textElem = document.getElementById(this.getID() + "-input");
        this.buttonElem = document.getElementById(this.getID() + "-button");
        this.buttonElem.addEventListener("click", this.onClick.bind(this));
    };

TextField.prototype.onClick =
    function()
    {
        var val = this.textElem.value;
        if(this.float) val = parseFloat(val);
        this.app.put(this.getPath(), val);
    };

Component.registerComponent(TextField);

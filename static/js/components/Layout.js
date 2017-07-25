function Layout(app, meta)
{
    Component.call(this, app, meta);
}

Layout.use =
    function(meta)
    {
        return !Component.utils.isLeaf(meta);
    };

Layout.prototype = new Component();

Layout.prototype.collapseContainer = null;
Layout.prototype.collapseDesc = null;
Layout.prototype.buttonSymbol = null;
Layout.prototype.hasOverall = false;
Layout.prototype.overall = null;
Layout.prototype.oldValue = false;

Layout.prototype.init =
    function()
    {
        var collapse = document.getElementById(`${this.getID()}-collapse`);
        if(collapse !== null)
        {
            collapse.addEventListener("click", this.toggleCollapsed.bind(this));
            this.collapseContainer = document.getElementById(`${this.getID()}-container`);
            this.collapseDesc = document.getElementById(`${this.getID()}-collapse-desc`);
            this.buttonSymbol = document.getElementById(`${this.getID()}-button-symbol`);
        }
        if(this.hasOverall)
            this.overall = document.getElementById(`${this.getID()}-overall`);
    };

Layout.prototype.update =
    function(data)
    {
        if(!this.hasOverall) return;
        if(data.overall === this.oldValue) return;

        this.oldValue = data.overall;
        this.overall.classList.remove("status-ok");
        this.overall.classList.remove("status-warn");

        if(data.overall === true || data.overall === "ok")
            this.overall.classList.add("status-ok");
        else if(data.overall === "warn")
            this.overall.classList.add("status-warn");        
    };

/*
Three layout modes: horizontal, vertical, tabular

Bottom level lists: horizontal
Bottom level dictionaries: vertical

Second level lists: tabular - level beneath gives rows
Second level dictionaries: horizontal

Third level lists: tabular - level beneath gives rows, final level vertical
Other: vertical
*/
Layout.prototype.generate =
    function(displayMode, tableHeaders)
    {
        //Sort children leaves/branches
        var leaves = [];
        var branches = [];

        //Guarantee overall is first and flag to add to title bar
        if(this.children.hasOwnProperty("overall") && this.children.overall.leaf)
        {
            leaves.push(this.children.overall);
            this.hasOverall = displayMode !== "main";
        }
    
        for(var key in this.children)
        {
            if(this.hasOverall && key === "overall") continue;

            if(this.children[key].leaf)
                leaves.push(this.children[key]);
            else
                branches.push(this.children[key]);
        }

        //Display mode not determined by preceeding layouts
        var height = Component.utils.height(this);
        var isList = this.meta instanceof Array;
        if(this.meta.hasOwnProperty("list"))
            isList |= this.meta.list;

        var main = false;
        if(displayMode === undefined)
        {
            if((height === 3 || height === 2) && isList)
                displayMode = "tabular";
            else if(height === 2 || (height === 1 && isList))
                displayMode = "horizontal";
            else
                displayMode = "vertical";
        }
        else if(displayMode === "main")
        {
            displayMode = "vertical";
            main = true;
        }

        var desc = null;
        if(this.meta.hasOwnProperty("description"))
            desc = this.meta.description;

        var ret = "";
        
        //Header containing collapse button, title and description where appropriate
        //Contains overall if present
        if(!main && displayMode !== "table_row" && displayMode !== "table_vertical")
        {
            ret += `
<div class="child-header">
    <div class="collapse-button" id="${this.getID()}-collapse">
        <div class="collapse-table">
            <span class="collapse-cell glyphicon glyphicon-triangle-bottom" id="${this.getID()}-button-symbol"></span>
        </div>
    </div>
    <h4>${this.getName()}</h4>`;
            if(this.hasOverall)
            {
                ret += `
<div class="status status-inline collapsed" id="${this.getID()}-overall"></div>`;
            }
            if(desc !== null)
            {
                ret += `
    <p class="inline-desc" id="${this.getID()}-collapse-desc"> - ${desc}</p>`;
            }
            ret += `
</div>`;
        }
        if(displayMode !== "table_row" && displayMode !== "table_vertical")
            ret += `
<div class="flex-container" id="${this.getID()}-container">`;

        //Generate HTML
        switch(displayMode)
        {
        case "vertical":
            //List leaves vertically in one column
            if(leaves.length || main)
            {
                ret += `
<div class="${height > 1 ? "parent-column" : "last"}">`;
                //Main column displays title and description
                if(main)
                {
                    ret += `
    <h4>${this.getName()}</h4>`;
                    if(desc !== null)
                    {
                        ret += `
    <p class="desc">
        ${desc}
    </p>`;
                    }
                }
                ret += `
    <div class="vertical">`;
                for(var leaf of leaves)
                {
                    ret += `
        <div>
            <h5>
                ${leaf.getName()}:
            </h5>
            <div class="variable-padding">
                <div class="padder"></div>
            </div>
            <div>
                ${leaf.generate()}
            </div>
        </div>`;
                }
                ret += `
    </div>
</div>`;
            }
            //List branches vertically in a second
            if(branches.length)
            {
                ret += `
<div class="child-column">`;
                for(var branch of branches)
                    ret += `
    <div class="child">
        ${branch.generate()}
    </div>`;
                ret += `
</div>`;
            }
            break;

        case "horizontal":
            //Include parent column with title and description
            if(leaves.length && height > 1)
            {
                ret += `
<div class="parent-column">`;
                if(desc !== null)
                {
                    ret += `
    <p class="desc">
        ${desc}
    </p>`;
                }
                ret += `
    <div class="vertical">`;
                for(var leaf of leaves)
                {
                    ret += `
        <div>
            <h5>
                ${leaf.getName()}:
            </h5>
            <div class="variable-padding">
                <div class="padder"></div>
            </div>
            <div>
                ${leaf.generate()}
            </div>
        </div>`;
                }
            ret += `
    </div>
</div>`;
            }
            //List leaves horizontally if height is 1
            else if(leaves.length)
            {
                ret += `
<div class="last">
    <div class="horizontal">`;
                for(var leaf of leaves)
                {
                    ret += `
        <div>
            <h5>
                ${leaf.getName()}:
            </h5>
            <div>
                ${leaf.generate()}
            </div>
        </div>`;
                }
            ret += `
    </div>
</div>`;
            }
            //List branches horizontally in separate column
            if(branches.length)
            {
                ret += `
<div class="child-column">`;
                for(var branch of branches)
                    ret += `
    <div class="flex-container">
        <div class="child">
            ${branch.generate()}
        </div>
    </div>`;
            ret += `
</div>`;
            }
            break;

        case "tabular":
            //Display branches as rows (THERE SHOULD BE NO LEAVES)
            ret += `
<div class="table-container">
    <table>
        <thead>
            <tr>
                <td></td>`;
            //Get headers from branches
            var headers = [];
            var printableHeaders = [];
            for(var branch of branches)
            {
                Array.prototype.push.apply(headers, Object.keys(branch.meta).map(
                    function(itm)
                    {
                        printableHeaders.push(Component.utils.getName(branch.meta, itm));
                        return itm;
                    }
                ));
            }
            printableHeaders = printableHeaders.filter(
                (itm, i, l) => 
                    ["name", "description", "list"].indexOf(headers[i]) === -1
                    && headers.indexOf(headers[i]) == i
            );
            headers = headers.filter(
                (itm, i, l) => 
                    ["name", "description", "list"].indexOf(itm) === -1
                    && l.indexOf(itm) == i
            );

            for(var header of printableHeaders)
                ret += `
                <th>${header}</th>`;
            ret += `
            </tr>
        </thead>
        <tbody>`;
            //Display branches
            for(var branch of branches)
                ret += `
            <tr>
                <th class="text-right">${branch.getName()}</th>
                ${branch.generate("table_row", headers)}
            </tr>`;
            ret += `
        </tbody>
    </table>
</div>`;
            break;

        case "table_row":
            //Display data in the table row matching headers correctly
            for(var header of tableHeaders)
            {
                if(this.children.hasOwnProperty(header))
                    ret += `
<td>${this.children[header].generate("table_vertical")}</td>`;
                else
                    ret += `
<td></td>`;

            }
            break;
        }
        
        if(displayMode !== "table_row" && displayMode !== "table_vertical")
            ret += `
</div>`;

        return ret;
    };

Layout.prototype.toggleCollapsed =
    function()
    {
        this.collapseContainer.classList.toggle("collapsed");
        this.buttonSymbol.classList.toggle("glyphicon-triangle-right");
        this.buttonSymbol.classList.toggle("glyphicon-triangle-bottom");
        if(this.collapseDesc !== null)
            this.collapseDesc.classList.toggle("collapsed");
        if(this.hasOverall)
            this.overall.classList.toggle("collapsed");
    }

Component.registerComponent(Layout);

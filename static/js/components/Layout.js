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
    function(displayMode)
    {
        //Sort children leaves/branches
        var leaves = [];
        var branches = [];
    
        for(var key in this.children)
        {
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

        if(displayMode === undefined)
        {
            if((height === 3 || height === 2) && isList)
                displayMode = "tabular";
            else if(height === 2 || (height === 1 && isList))
                displayMode = "horizontal";
            else
                displayMode = "vertical";
        }

        var desc = null;
        if(this.meta.hasOwnProperty("description"))
            desc = this.meta.description;

        var ret = "";

        //Generate HTML
        switch(displayMode)
        {
        case "vertical":
            if(leaves.length || desc !== null)
            {
                ret += `
<div class="${height > 1 ? "parent-column" : "last"}">
    <h4>${this.getName()}</h4>`;
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
            <div>
                ${leaf.generate()}
            </div>
        </div>`;
                }
                ret += `
    </div>
</div>`;
            }
            else
            {
                ret += `
<h4>${this.getName()}</h4>`;
            }
            if(branches.length)
            {
            ret += `
<div class="child-column">`;
            for(var branch of branches)
                ret += `
    <div class="float-container">
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
<div class="parent-column">
    <h4>${this.getName()}</h4>`;
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
            <div>
                ${leaf.generate()}
            </div>
        </div>`;
                }
            ret += `
    </div>
</div>`;
            }
            //List leaves horizontally with description and title above
            else if(leaves.length)
            {
                ret += `
<div class="last">
    <h4>${this.getName()}</h4>`;
                if(desc !== null)
                {
                    ret += `
        <p class="desc">
            - ${desc}
        </p>`;
                }
                ret += `
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
    <div class="float-container">
        ${branch.generate()}
    </div>`;
            ret += `
</div>`;
            }
            break;

        case "tabular":
            ret += `
<h4>${this.getName()}</h4>
<table>
    <thead><tr></tr></thead><!--TODO: Add table headers-->
    <tbody>`;
            for(var branch of branches)
                ret += `
        <tr>
            <th>${branch.getName()}</th>
            ${branch.generate("table_row")}
        </tr>`;
            ret += `
    </tbody>
</table>`;
            break;

        case "table_row":
            for(var branch of branches)
                ret += `
<td>${branch.generate("vertical")}</td>`;
            for(var leaf of leaves)
                ret += `
<td>${leaf.generate()}</td>`;
            break;
        }

        return ret;
    };

Component.registerComponent(Layout);

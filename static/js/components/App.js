function App()
{
    this.mount = document.getElementById("app");
    this.current_adapter = 0;
    this.adapters = {};
    this.error_message = null;
    this.error_timeout = null;

    //Retrieve metadata for each adapter
    var meta = {};
    var promises = adapters.map(
        function(adapter, i)
        {
            return apiGET(i, "", true).then(
                function(data)
                {
                    meta[adapter] = data;
                }
            );
        }
    );

    //Then generate the page and start the update loop
    $.when.apply($, promises)
    .then(
        (function()
        {
            this.generate(meta);
            setTimeout(this.update.bind(this), this.update_delay * 1000);
        }).bind(this)
    );
}

App.prototype.freq_overlay = null;
App.prototype.query_overlay = null;
App.prototype.update_delay = 0.2;

//Submit GET request then update the current adapter with new data
App.prototype.update =
    function()
    {
        var updating_adapter = this.current_adapter;
        apiGET(updating_adapter, "", false)
        .done(
            (function(data)
            {
                this.adapters[adapters[updating_adapter]].update(data);
                setTimeout(this.update.bind(this), this.update_delay * 1000);
            }).bind(this)
        )
        .fail(this.setError.bind(this));
    };


//Construct page and call components to be constructed
App.prototype.generate =
    function(meta)
    {
        //Construct navbar
        var navbar = document.createElement("nav");
        navbar.classList.add("navbar");
        navbar.classList.add("navbar-inverse");
        navbar.classList.add("navbar-fixed-top");
        navbar.innerHTML = `
<div class="container-fluid">
    <div class="navbar-header">
        <div class="navbar-brand">
            Odin Server
        </div>
    </div>
    <div class="navbar-brand navbar-logo">
        <img class="navbar-brand logo" src="img/stfc_logo.png">
    </div>
    <ul class="nav navbar-nav" id="adapter-links"></ul>

    <ul class="nav navbar-nav navbar-right">
        <li class="dropdown">
            <a class="dropdown-toggle" href=# data-toggle="dropdown">
                Options
                <span class="caret"></span>
            </a>
            <ul class="dropdown-menu">
                <li><a href="#" id="update-freq">Update Frequency</a></li>
                <li><a href="#" id="toggle-dark">Toggle Dark</a></li>
                <li><a href="#" id="raw-query">Raw Query</a></li>
            </ul>
        </li>
    </ul>
</div>`;
        this.mount.appendChild(navbar);
        document.getElementById("update-freq").addEventListener("click", this.updateFrequency.bind(this));
        document.getElementById("toggle-dark").addEventListener("click", this.toggleDark.bind(this));
        document.getElementById("raw-query").addEventListener("click", this.rawQuery.bind(this));
        var nav_list = document.getElementById("adapter-links");

        //Create error bar
        var error_bar = document.createElement("div");
        error_bar.classList.add("error-bar");
        this.mount.appendChild(error_bar);
        this.error_message = document.createTextNode("");
        error_bar.appendChild(this.error_message);

        //Add adapter pages
        for(var key in meta)
        {
            //Create DOM node for adapter
            var container = document.createElement("div");
            container.id = "adapter-" + key;
            container.classList.add("adapter-page");
            this.mount.appendChild(container);

            var adapter_name = Component.utils.getName(meta, key);
            this.adapters[key] = new Adapter(this, container, adapter_name, meta[key]);

            //Update navbar
            var list_elem = document.createElement("li");
            nav_list.appendChild(list_elem);
            var link = document.createElement("a");
            link.href = "#";
            list_elem.appendChild(link);
            var link_text = document.createTextNode(adapter_name);
            link.appendChild(link_text);
            
            link.addEventListener("click", this.changeAdapter.bind(this, [adapters.indexOf(key)]));
        }

        document.getElementById("adapter-" + adapters[this.current_adapter]).classList.add("active");

        //Add overlays
        //Change frequency
        this.freq_overlay = document.createElement("div");
        this.freq_overlay.classList.add("overlay-background");
        this.freq_overlay.classList.add("hidden");
        this.freq_overlay.innerHTML = `
<div class="overlay">
    <h5>Set the frequency to update the webpage:</h5>
    <div>
        <div class="input-group">
            <input class="form-control text-right" id="frequency-value" placeholder="5" type="text">
            <span class="input-group-addon">Hz</span>
        </div>
        <div class="overlay-control-buttons">
            <button class="btn btn-success" id="frequency-set" type="button">Set</button>
            <button class="btn btn-danger" id="frequency-cancel" type="button">Cancel</button>
        </div>
    <div>
</div>
`;
        this.mount.appendChild(this.freq_overlay);
        document.getElementById("frequency-cancel").addEventListener("click", this.frequencyCancel.bind(this));
        document.getElementById("frequency-set").addEventListener("click", this.frequencySet.bind(this));

        //Raw query
        this.query_overlay = document.createElement("div");
        this.query_overlay.classList.add("overlay-background");
        this.query_overlay.classList.add("hidden");
        this.query_overlay.innerHTML = `
<div class="overlay">

</div>
`;
        this.mount.appendChild(this.query_overlay);


        //Add footer
        var footer = document.createElement("div");
        footer.classList.add("footer");
        footer.innerHTML = `
Odin server: <a href="www.github.com/odin-detector/odin-control">www.github.com/odin-detector/odin-control</a>`;
        this.mount.appendChild(footer);
    };

//Handles onClick events from the navbar
App.prototype.changeAdapter =
    function(adapter)
    {
        document.getElementById("adapter-" + adapters[this.current_adapter]).classList.remove("active");
        document.getElementById("adapter-" + adapters[adapter]).classList.add("active");

        this.current_adapter = adapter;
    };

App.prototype.setError =
    function(data)
    {
        var json = data.responseJSON;
        if(json.hasOwnProperty("error"))
        {
            if(this.error_timeout !== null) clearTimeout(this.error_timeout);
            this.error_message.nodeValue = `Error: ${json.error}`;
            this.error_timeout = setTimeout(this.clearError.bind(this), 5000);
        }
 
    }

App.prototype.clearError =
    function()
    {
        this.error_message.nodeValue = "";
    };

App.prototype.put =
    function(path, val)
    {
        apiPUT(this.current_adapter, path, val)
        .fail(this.setError.bind(this));
    };

App.prototype.updateFrequency =
    function()
    {
        document.getElementById("frequency-value").placeholder = (Math.round(100 / this.update_delay) / 100).toString();
        this.freq_overlay.classList.remove("hidden");
    };

App.prototype.frequencyCancel =
    function()
    {
        this.freq_overlay.classList.add("hidden");
    };

App.prototype.frequencySet =
    function()
    {
        var val = document.getElementById("frequency-value").value;
        this.update_delay = 1 / parseFloat(val);
        this.freq_overlay.classList.add("hidden");        
    };

App.prototype.toggleDark =
    function()
    {
        this.mount.classList.toggle("dark");
    };

App.prototype.rawQuery =
    function()
    {
        this.query_overlay.classList.remove("hidden");
    };

//Create the App() instance
function initApp()
{
    var app = new App();
}

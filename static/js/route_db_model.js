'use strict'
//Class Location
function Location(data){
    var sg_postal_len = 6;
    var properties = ["address", "postal", "city", "state", "country"];
    
    init_obj(this, "Location", properties, data);
    
    //For SG address, either use postal code or address for OneMap query
    if (this.country === "Singapore"){
        if(this.postal){
            this.postal.trim();
            this.postal = pad_str(this.postal, "0", sg_postal_len);
            this.onemap_address = this.postal;
        }
        else {
            this.onemap_address = format_address(this.address);   
        }
    }
    
    if (this.address)
        this.full_address = this.address + ", ";
    else
        this.full_address ="";

    if (this.postal)
        this.full_address += this.postal + ", ";

    if (this.city)
        this.full_address += this.city + ", ";

    if (this.state)
        this.full_address += this.state + ", ";

    this.full_address += this.country;
    //this.full_address = format_address(this.full_address);
    
    if (this.onemap_address) {
        this.map_provider = MAPGEOCODER.onemap;
    }
    else {
        this.map_provider = MAPGEOCODER.google;
    }

}
Location.prototype.get_loc_latlng = function(latlng_handler){
    var addr;
    
    if (this.onemap_address) {
        addr = this.onemap_address;
    }
    else {
        addr = this.full_address;
    }

    var _this = this;
    
    //console.log("before geocode....");
    //print_obj(_this);
    
    _this.map_provider.geocode(addr, function(result){
        var r = result[0];
        if (r){
            _this.lat = r.latitude;
            _this.lng = r.longitude;
            
            if (typeof latlng_handler.loc_latlng_callback === 'function')
                latlng_handler.loc_latlng_callback(_this);
        }             
    });
}
//Get the direction between the previous location and this location
Location.prototype.get_loc_direction = function(pre_loc, direction_handler){
    var direction_summary = {}
    direction_summary.latlngs = [];
    direction_summary.total_time = 0;
    direction_summary.distance = 0;
    
    
    if (this.lat === pre_loc.lat && this.lng === pre_loc.lng) {
        this.direction_summary = direction_summary;
        return;
    }
    
    var loc_array = [];
    loc_array.push(pre_loc.get_loc_str());
    loc_array.push(this.get_loc_str());
    
    var _this = this;
    
    _this.map_provider.get_direction(loc_array, function(result){
        
        
        if (result === false){
            _this.direction_summary = {};
            _this.direction_summary.latlngs = [];
            _this.direction_summary.total_time = 0;
            _this.direction_summary.distance = 0;
            return;
        }
        
        _this.direction_summary = {};
        _this.direction_summary.latlngs = L.GeoJSON.coordsToLatLngs(result.paths);
        _this.direction_summary.total_time = result.total_time;
        _this.direction_summary.distance = result.distance;
         
        if (typeof direction_handler.loc_direction_callback === 'function')
                direction_handler.loc_direction_callback(_this);
    });
}

Location.prototype.get_loc_str = function(){
    var loc_str;
    /*if (this.lat){
        loc_str = this.lng + "," + this.lat;
    }
    else*/
    if (this.onemap_address)
        loc_str = this.onemap_address;
    else
        loc_str = this.full_address;
    
    return loc_str;
}
Location.prototype.get_direction_summary = function(){
    if (typeof this.direction_summary === undefined)
        return false;
    else;
        return this.direction_summary;
}

//Class TimeWindow
function TimeWindow(data){
    var properties = ["_date_format"];
    init_obj(this, "TimeWindow", properties, data);
    
    if (!data._tm_window_date){
        this._tm_window_date = moment().format("YYYY-MM-DD");
    }
    else{
        this._tm_window_date = moment(data._tm_window_date, this._date_format).format("YYYY-MM-DD");
    }
    
    this._start_tm_slot = convert_to_24h(data._start_tm_slot, "21:00");
    this._end_tm_slot = convert_to_24h(data._end_tm_slot, "23:00");
    this.start_tm = covert_to_second(this._tm_window_date, this._start_tm_slot);
    this.end_tm = covert_to_second(this._tm_window_date, this._end_tm_slot);
}
TimeWindow.prototype.get_start_tm = function(){
    return this.start_tm;
}

TimeWindow.prototype.get_end_em = function (){
    return this.end_tm;
}

//Class Task
function Task(data) {
    var properties = ["task_id"];
    init_obj(this, "Task", properties, data);
}
Task.prototype.set_destination = function(dest){
    this.destination = dest;
}
Task.prototype.set_delivery_tm_window = function(tm_window){
    this.delivery_tm_window = tm_window;
}
Task.prototype.get_task_latlng = function(latlng_handler){
    //Based on the loc_key to decide which location to call
    var loc_key = latlng_handler.loc_key;
    var loc = this[loc_key];
    if (typeof latlng_handler.task_latlng_callback === 'function')
        loc = latlng_handler.task_latlng_callback(this, loc);
    loc.get_loc_latlng(latlng_handler);
}

Task.prototype.get_task_direction = function(pre_task, direction_handler){
    //Based on the loc_key to decide which location to call
    var loc_key = direction_handler.loc_key;
    var loc = this[loc_key];
    var pre_loc = pre_task[loc_key];
    loc.get_loc_direction(pre_loc, direction_handler);
}
Task.prototype.get_direction_summary = function(direction_handler){
    var loc_key = direction_handler.loc_key;
    var loc = this[loc_key];
    return loc.get_direction_summary();
}

//Class Vehicle
function Vehicle(data){
    var route = {};
    var properties = ["vehicle_id"];
    init_obj(this, "Vehicle", properties, data);
    if (typeof this.vehicle_id === undefined)
        this.vehicle_id = "example";
}
Vehicle.prototype.set_route = function(route){
    this.route = route;
}
Vehicle.prototype.get_route = function(){
    return this.route;
}
Vehicle.prototype.add_task = function(task){
    this.route.push(task);
}
/*
* This function sorts the json array based on timestamp
* It first sort by the start_tm then by end_tm
*/
Vehicle.prototype.sort_route_by_delivery_tm = function(){
    this.route.sort(function(a,b) {
        if (a.delivery_tm_window.start_tm !== b.delivery_tm_window.start_tm){
            return a.delivery_tm_window.start_tm - b.delivery_tm_window.start_tm;
        }
        else{
            return a.delivery_tm_window.end_tm - b.delivery_tm_window.end_tm;
        }
    });
}
/*
* This function filter the route based on start and end time
*/
Vehicle.prototype.filter_route_by_delivery_tm = function(start_tm, end_tm){
    this.route = this.route.filter(function(a){
        /*
        * check the timestamp and reject the below cases:
        * 1. task end before the start_tm
        * 2. task start after the end_tm
        */
        if ( a.delivery_tm_window.end_tm < start_tm || 
             a.delivery_tm_window.start_tm > end_tm
           )
            return false;
        else
            return true;
    });
}
Vehicle.prototype.get_route_latlngs = function(time_delay, latlng_handler){
    
    var t_max_no = this.route.length;
    if (typeof latlng_handler !== undefined)
        if (t_max_no > latlng_handler.max_per_route)
            t_max_no = latlng_handler.max_per_route;
    
    var total_time_delay = 0;
    
    for (var idx = 0 ; idx < t_max_no; idx++){
        var task = this.route[idx];

        setTimeout(function(_vehicle, _task, _counter){
            //console.log("Vehicle.prototype.get_route_latlngs " + _counter);
            
            if (typeof latlng_handler.vehicle_latlng_callback === 'function')
                _task = latlng_handler.vehicle_latlng_callback(_vehicle, _task, _counter);
            
            _task.get_task_latlng(latlng_handler);
            
        }, total_time_delay, this, task, idx);
        
        total_time_delay += time_delay;
    }
}

Vehicle.prototype.get_route_directions = function(time_delay, direction_handler) {
    
    var t_max_no = this.route.length;
    if (typeof direction_handler !== undefined)
        if (t_max_no > direction_handler.max_per_route)
            t_max_no = direction_handler.max_per_route;
    
    var total_time_delay = 0;
    
    if (t_max_no < 2)
        return "Required at least 2 locations to get driving direction!";
    
    //Start from the 2nd task as it required at least 2 locations
    for (var idx = 1 ; idx < t_max_no; idx++) {
        var task = this.route[idx];
        var pre_task = this.route[idx -1];
        
        setTimeout(function(_task, _pre_task){
            _task.get_task_direction(_pre_task, direction_handler);
        }, total_time_delay, task, pre_task);
        
        total_time_delay += time_delay;
    }
}

Vehicle.prototype.get_directions_summary = function(direction_handler){
    var t_max_no = this.route.length;
    if (typeof direction_handler !== undefined)
        if (t_max_no > direction_handler.max_per_route)
            t_max_no = direction_handler.max_per_route;
    var directions_summary = {};
    directions_summary.total_time = 0;
    directions_summary.distance = 0;
    this.directions_summary = directions_summary;
    
    //Check if all the task has direction summary for every 10 secs
    var cal_direction_summary = setInterval(function(_this) {
        _this.directions_summary.total_time = 0;
        _this.directions_summary.distance = 0;

        for (var idx = 1 ; idx < t_max_no; idx++) {
            var task = _this.route[idx];
            var ds = task.get_direction_summary(direction_handler);
        
            //if one of the task doesn't have the summary, stop the calculation and wait for the next time
            if ( ds === false) 
                return;
            else {
                _this.directions_summary.total_time += Number(ds.total_time);
                _this.directions_summary.distance += Number(ds.distance);
            }
        }//End of for 
        
        //If all the task has the summary, clear the timer and callback
        clearInterval(cal_direction_summary);
        clearTimeout(myTimer);
        
        if (typeof direction_handler.route_directions_summary_callback === 'function')
            direction_handler.route_directions_summary_callback(_this);

    }, 10000, this);
    
    //Clear it anyway after a long wait
    var myTimer = setTimeout(function(_this){
        
        clearInterval(cal_direction_summary);
        _this.directions_summary.total_time = 0;
        _this.directions_summary.distance = 0;
        
        if (typeof direction_handler.route_directions_summary_callback === 'function')
                direction_handler.route_directions_summary_callback(_this);
    }, 300000, this);
}
/*Vehicle.prototype.get_route_latlngs = function(time_delay, latlng_handler, params){
    var t_max_no = this.route.length;
    var _this  = this;
    var _total_time_delay = 0;
    

    function each_task_latlng(_counter){
        setTimeout(function(){
            if (_counter >= t_max_no)
                return;
            
            var _task = _this.route[_counter];
            var params = v_handler.task_handler(_task, _counter, params);
            _task.get_loc_latlng(loc_key, v_handler);

            _counter++;
            _total_time_delay += time_delay;
            each_task_latlng(_counter);
            
        }, _total_time_delay);
    }
    each_task_latlng(0);
}*/

//Class ClosePlan
function ClosedPlan(fleet) {
    this.fleet = fleet;
}
ClosedPlan.prototype.get_fleet = function(){
    return this.fleet;
}
//Set the dataTable format of the plan
ClosedPlan.prototype.set_dt_form = function(_dt_form){
    this._dt_form = _dt_form;
}
ClosedPlan.prototype.get_dt_form = function(){
    return this._dt_form;
}
ClosedPlan.prototype.create_dt_form = function(){
    this._dt_form = [];
    for (var v_idx = 0; v_idx < this.fleet.length; v_idx++){
        var vehicle = this.fleet[v_idx];
        var vehicle_id = vehicle.vehicle_id;
        for (var t_idx = 0; t_idx < vehicle.route.length; t_idx++){
            var task = vehicle.route[t_idx];
            var _dt_obj = {};
            _dt_obj.vehicle_id = vehicle_id;
            _dt_obj.task = task;
            this._dt_form.push(_dt_obj);
        }
    }
}
ClosedPlan.prototype.get_fleet_latlngs = function(time_delay, latlng_handler){
    var v_max_no = this.fleet.length;
    if (typeof latlng_handler !== undefined)
        if (v_max_no > latlng_handler.max_route_no)
            v_max_no = latlng_handler.max_route_no;
    
    var total_time_delay = 0;
    
    for (var idx = 0; idx < v_max_no; idx++){
        
        var vehicle = this.fleet[idx];
        var route_size = vehicle.get_route().length;
        
        if (route_size > latlng_handler.max_per_route)
            route_size = latlng_handler.max_per_route;
        
        setTimeout(function( _delay, _vehicle, _counter){
            //console.log("ClosedPlan.prototype.get_fleet_latlngs for vehicle " + _counter + " at time " + _total_time_delay);
            
            if (typeof latlng_handler.fleet_latlng_callback === 'function')
                _vehicle = latlng_handler.fleet_latlng_callback(_vehicle, _counter);
            
            _vehicle.get_route_latlngs(_delay, latlng_handler);
            
        }, total_time_delay, time_delay, vehicle, idx);
        
        total_time_delay += route_size * time_delay
    }
}

ClosedPlan.prototype.get_fleet_directions = function(time_delay, direction_handler) {
    var v_max_no = this.fleet.length;
    
    if (typeof direction_handler !== undefined)
        if (v_max_no > direction_handler.max_route_no)
            v_max_no = direction_handler.max_route_no;
    
    var total_time_delay = 0;
    
    for (var idx = 0; idx < v_max_no; idx++){
        
        var vehicle = this.fleet[idx];
        var route_size = vehicle.get_route().length;
        
        if (route_size > direction_handler.max_per_route)
            route_size = direction_handler.max_per_route;
        
        //To set delay between get_latlng and get_direction
        total_time_delay += route_size * time_delay;
        
        setTimeout(function(_delay, _vehicle){
            _vehicle.get_route_directions(_delay, direction_handler);
        }, total_time_delay, time_delay, vehicle);
    }
}

ClosedPlan.prototype.get_fleet_directions_summary = function(time_delay, direction_handler) {
    var v_max_no = this.fleet.length;
    var total_time_delay = 0;
    
    if (typeof direction_handler !== undefined)
        if (v_max_no > direction_handler.max_route_no)
            v_max_no = direction_handler.max_route_no;
    
    for (var idx = 0; idx < v_max_no; idx++){
        var vehicle = this.fleet[idx];
        
        var route_size = vehicle.get_route().length;
        if (route_size > direction_handler.max_per_route)
            route_size = direction_handler.max_per_route;
        
        total_time_delay += route_size * time_delay;
        
        setTimeout(function(_vehicle){
            //console.log("ClosedPlan.prototype.get_fleet_directions_summary at" + _total_time_delay);
            _vehicle.get_directions_summary(direction_handler);
        }, total_time_delay, vehicle);
    }
}

/*ClosedPlan.prototype.get_fleet_latlngs = function(route_size, time_delay, loc_key, vehicle_handler){
    var v_max_no = this.fleet.length;
    if (v_max_no > route_size)
        v_max_no = route_size;
    
    var _this  = this;
    var _total_time_delay = 0;
    
    
    function each_vehicle_latlngs(_counter){
        setTimeout(function(){
            if (_counter >= v_max_no)
                return;
            var _vehicle = _this.fleet[_counter];
            //var _route = _this.fleet[_counter].get_route();
            var _route_size = _this.fleet[_counter].get_route().length;
            //console.log("Calling ClosedPlan.get_fleet_latlngs after " + _total_time_delay);
            
            var v_handler = new vehicle_handler(_vehicle, _counter);
            _vehicle.get_route_latlngs(time_delay, loc_key, v_handler);
            
            
            _counter++;
            _total_time_delay += _route_size * time_delay;
            each_vehicle_latlngs(_counter);
            
        }, _total_time_delay);
    }
    each_vehicle_latlngs(0);
}*/

/*
*   A general initilization function for route class
*   It accept a html_map, in which:
*       key is html_tag_id: the id used in html
*       val is the value that going to set in the object
*   It will rely on the global variable ROUTE_PLAN_HTML
*   to decide the property for the object
*/
function init_obj (obj, cls_name, property_array, html_map){
    //Go through the ROUTE_PLAN_HTML to construct the data for the object

    for (var html_tag_id in html_map){
        //console.log("find html_tag_id : " + html_tag_id);
        //Get the property definition
        if (html_tag_id in ROUTE_PLAN_HTML) {
            var obj_def = ROUTE_PLAN_HTML[html_tag_id];
            //console.log("find obj_def : " + obj_def);
            
            //If the property belogs to this class
            if (obj_def.cls === cls_name) {
                //console.log("class matching : " + cls_name);
                
                //If there is a match between the input and the property_array
                if ( $.inArray(obj_def.prop_name, property_array) !== -1)
                    //console.log("find prop_name : " + obj_def.prop_name);
                    
                    obj[obj_def.prop_name] = html_map[html_tag_id];
                }
            }
        }//End of for
    //print_obj(obj);
    return obj;
}//End of function init_obj


//Format the address to make work is separated by one space only
function format_address(addr_str){
    if (addr_str){
        addr_str = addr_str.replace(/,/g, " ");
        addr_str = addr_str.replace(/ +/g, " ");
        return addr_str;
    }
}

'use strict'
//Class Location
function Location(data){
    var sg_postal_len = 6;
    var properties = ["address", "postal", "city", "state", "country"];
    
    init_obj(this, properties, data);
    
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

}
//Set class variable, for dataTable display

Location.key_name = "location";
Location.address = Location.key_name +"."+"address";
Location.postal = Location.key_name +"."+"postal";
Location.city = Location.key_name +"."+"city";
Location.state = Location.key_name +"."+"state";
Location.country = Location.key_name +"."+"country";



//Class Order
function Delivery_Time(data){
    var properties = ["date_format"];
    init_obj(this, properties, data);
    
    if (!data.delivery_date){
        this.delivery_date = moment().format("YYYY-MM-DD");
    }
    else{
        this.delivery_date = moment(data.delivery_date, this.date_format).format("YYYY-MM-DD");
    }
    
    this.start_tm_slot = convert_to_24h(data.start_tm_slot, "21:00");
    this.end_tm_slot = convert_to_24h(data.end_tm_slot, "23:00");
    this.start_tm = covert_to_second(this.delivery_date, this.start_tm_slot);
    this.end_tm = covert_to_second(this.delivery_date,this.end_tm_slot);
}
Delivery_Time.key_name = "d_time";
Delivery_Time.delivery_date = Delivery_Time.key_name + "." + "delivery_date";
Delivery_Time.start_tm_slot = Delivery_Time.key_name + "." + "start_tm_slot";
Delivery_Time.end_tm_slot = Delivery_Time.key_name + "." + "end_tm_slot";

//Class Fleet
function Fleet(data){
    var properties = ["fleet_no"];
    init_obj(this, properties, data);
}
Fleet.key_name = "fleet";
Fleet.fleet_no = Fleet.key_name + "." + "fleet_no";

//Class Plan
function Plan(loc_array){
    this.loc_array = loc_array;
    this.no_of_loc = loc_array.length;
}

//Get all the latlng for locations, each request pause based on time_delay
Plan.prototype.get_latlngs = function(time_delay) {
    var counter = 0;
    var search_str;
    var _this = this;
    
    function each_latlng(){
        setTimeout(function(){
            if (counter >= _this.no_of_loc)
                return;
            var tmp_loc = _this.loc_array[counter];
            
            if (tmp_loc.onemap_address){
                MapGeocoder = onemapAPI;
                search_str = tmp_loc.onemap_address;
            }
            else {
                MapGeocoder = googleAPI;
                search_str = tmp_loc.full_address;
            }
            
            _this.get_latlng(counter, search_str);
            counter++;
            each_latlng();
        }, time_delay);
    };
    each_latlng();
}

Plan.prototype.get_latlng = function(idx, search_str){
    var _this = this;
    MapGeocoder.geocode(search_str, function(result) {
        //console.log(idx + ": " + search_str);
        var r = result[0];
        if (r){
            _this.loc_array[idx].lat = r.latitude;
            _this.loc_array[idx].lng = r.longitude;
        }
        //console.log(counter);
        //print_obj(_this.loc_array[idx]);
    });
}
    
    

//General functions
function init_obj (obj, property_array, obj_map){
    for (var idx = 0; idx < property_array.length; idx++){
        var key = property_array[idx];
           if (key in obj_map)
               obj[key] = obj_map[key]
    }
}
//Add the column definition into the dataTableMap
function add_dt_col_def(cls){
    //add all the class variables
    var key;
    for (key in cls){
        if(key != "key_name" && typeof cls[key] !== "function") 
        {
            DataTableMap[key] = cls[key];
        }
    }
}

//Format the address to make work is separated by one space only
function format_address(addr_str){
    addr_str = addr_str.replace(/,/g, " ");
    addr_str = addr_str.replace(/ +/g, " ");
    return addr_str;
}

var DataTableMap = {
    //property_name: Class.property_name
};

add_dt_col_def(Location);
add_dt_col_def(Delivery_Time);
add_dt_col_def(Fleet);
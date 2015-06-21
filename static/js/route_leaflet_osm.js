/*
leaflet wrapper for OpenStreetMap 
*/

//Define CONSTANT

//MapQuest OSM Tiles
var TILE_URL_TEMPLATE = 'http://{s}.mqcdn.com/tiles/1.0.0/map/{z}/{x}/{y}.png';
var ATTRIBUTION = '&copy; <a href="http://osm.org/copyright" title="OpenStreetMap" target="_blank">OpenStreetMap</a> | Tiles Courtesy of <a href="http://www.mapquest.com/" title="MapQuest" target="_blank">MapQuest</a> <img src="http://developer.mapquest.com/content/osm/mq_logo.png" width="16" height="16"> | Data &copy <a href="http://www.onemap.sg/" title="ONEMAP" target="_blank">ONEMAP</a>" <img src="http://t1.onemap.sg/api/js/imap_small_logo.gif" style="vertical-align:bottom">';
var SUBDOMAINS = ['otile1','otile2','otile3','otile4'];
var TILE_LAYER_OPTIONS = {
        minZoom: 2,
		attribution:ATTRIBUTION, 
		subdomains: SUBDOMAINS,
	};

var COLOR_ARRAY = ["purple", "blue", "crimson", "lightskyblue", "orange", "violet", "yellow", "brown", "green", "palegreen"];
var NUM_ICON_PATH = "/img/leaflet/map_icons/numbers";
var MAX_NUM_PER_ROUTE = 100;
//var MAP_GEOCODER = new OneMapProvider();
var OSM_MAP;
var TRUCK_IMG = "truck.png";
var REQ_PER_MIN = 10;//-1 means no limit
var mapVar = mapVar || {};

var googleAPI = new GeocoderJS.createGeocoder({'provider': 'google'});
var yandexAPI =  new GeocoderJS.createGeocoder('yandex');
var onemapAPI = new OneMapProvider();
var MAPGEOCODER = {
    onemap : onemapAPI,
    google : googleAPI,
    yandex : yandexAPI
};

function create_icon (color, number){
    //console.log("creating icon" + NUM_ICON_PATH+'/'+color+'/'+'number_'+number+'.png');
	var icon = L.icon({
	    iconUrl:	  NUM_ICON_PATH+'/'+color+'/'+'number_'+number+'.png',
	    iconSize:     [25, 25], // size of the icon
	    iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
	    popupAnchor:  [2, 2] // point from which the popup should open relative to the iconAnchor
		});
    
    
	return icon;
}

/*
Create an OpenStreetMap with the following params:
div_id: id of the div element which contains the map, 
	make sure the element has a defined height
center: array to hold the geocode for the map center
level: zoom level
*/
function create_osmap(map_opts){
	var div_id = map_opts.div_id;
	var center = map_opts.center;
	var zoom = map_opts.zoom;
    var loc = {
		lat: 1.443930,
		lng: 103.785256
	}
    
	if (center === undefined) {
		center = [loc.lat, loc.lng];
	}
    if (OSM_MAP)
        OSM_MAP.remove();
    
    var map = L.map(div_id);
    OSM_MAP = map;
    map.on('locationerror', {map: map, center:center, zoom:zoom}, handleLocationError);
    
    map.locate({setView: true, maxZoom: zoom});
    L.tileLayer(TILE_URL_TEMPLATE,TILE_LAYER_OPTIONS).addTo(map);
    return map;
}//End of create_osmap

function handleLocationError(e){
    console.log("not able to locate");
    e.data.map.setView(e.data.center, e.data.zoom);
}
/*
* Show the routes on the map
* 1. Create an openstreet map
* 2. Determine the number of route shown on map
* 3. Make sure the location on each route doesn't exceed the allowed max number
* 4. For each location:
* 4.1 Retrieve the icon
* 4.2 Add to map
*/
function show_routes_osmap(map_opts, closed_plan, multi_route_warning_id, color_legend_id){
    var map = create_osmap(map_opts);
    var time_delay;
    
    if (REQ_PER_MIN == -1)
        time_delay = 10;
    else
        time_delay = (1000/REQ_PER_MIN);
    
    var color_size = COLOR_ARRAY.length;
    var route_size = closed_plan.get_fleet().length;
    
    if (route_size >= color_size) {
        show_item(multi_route_warning_id);
        route_size = color_size;
    }
    
    var map_legend_item = $(color_legend_id);
    //Make sure the map_legend is empty
    map_legend_item.empty();
    
    
    //Define map handler which include constant and various callback for map generation
    var map_handler = {};
	map_handler.loc_key = "destination";
	map_handler.max_per_route = MAX_NUM_PER_ROUTE;
	map_handler.max_route_no = route_size;
    
    /* Fleet: based on the counter to set the color
    *  and truck imag for the vehicle.
    */
	map_handler.fleet_latlng_callback = function (vehicle, counter) {
        //console.log("fleet_latlng_callback for vehicle " + counter)

        var icon_color = COLOR_ARRAY[counter];
        vehicle.icon_color = icon_color;
        return vehicle
	}

	map_handler.vehicle_latlng_callback = function (vehicle, task, counter){
        //console.log("vehicle_latlng_callback task " + counter);
        
        task.vehicle_id = vehicle.vehicle_id;
        task.icon_color = vehicle.icon_color;
        task.seq = counter + 1;
        
        return task;
	}
    
    map_handler.task_latlng_callback = function (task, loc){

        loc.vehicle_id = task.vehicle_id;
        loc.icon_color = task.icon_color;
        loc.seq = task.seq;
        return loc;
    }

	map_handler.loc_latlng_callback = function (loc) {
		//console.log("loc_latlng_callback for location");
        
        var icon = create_icon(loc.icon_color, loc.seq);
        var marker;
        var popup_str = "Vehicle : " + loc.vehicle_id + "  Address: "+ loc.full_address;
        if (loc.lat){
            var center = [loc.lat, loc.lng];
            if (icon){
                marker = L.marker(center, {icon:icon}).addTo(map);
            }
            else {
                marker = L.marker(center).addTo(map);
            }
            marker.bindPopup(popup_str);
        }
	}
    
    map_handler.loc_direction_callback = function (loc) {
        //console.log("loc_direction_callback for location");
        
        var latlngs = loc.direction_summary.latlngs;
        var total_time = loc.direction_summary.total_time.toFixed(2);
        var distance = loc.direction_summary.distance.toFixed(2);
        
        var polyline = L.polyline(latlngs, {color: loc.icon_color}).addTo(map);
        
        var popup_str = "The distance between the 2 locations is: " + distance + " km. The travel time is " + total_time + " mintues."; 
        polyline.bindPopup (popup_str);
           
    }

    map_handler.route_directions_summary_callback = function(vehicle){
        //console.log("route_directions_summary_callback for vehicle");
        var truck_img = NUM_ICON_PATH+'/'+vehicle.icon_color+'/'+TRUCK_IMG;
        var total_time = vehicle.directions_summary.total_time.toFixed();
        var distance = vehicle.directions_summary.distance.toFixed();
        
        map_legend_item.append('<td>' + vehicle.vehicle_id + 
                               '<img src=' + truck_img+ '><p>' 
                               + distance + ' km <p>'+ total_time + ' mins </td>');
        //print_obj(vehicle);
    }
    
    closed_plan.get_fleet_latlngs(time_delay, map_handler);
    closed_plan.get_fleet_directions(time_delay*10, map_handler);
    closed_plan.get_fleet_directions_summary(time_delay*10, map_handler);
    
    return map;
}




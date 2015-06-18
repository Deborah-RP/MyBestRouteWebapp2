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

var COLOR_ARRAY = ["crimson", "lightskyblue", "orange", "violet", "yellow", "blue", "brown", "green", "lightyellow", "purple"];
var NUM_ICON_PATH = "/img/leaflet/map_icons/numbers";
var MAX_NUM_PER_ROUTE = 100;
//var MAP_GEOCODER = new OneMapProvider();
var OSM_MAP;
var TRUCK_IMG = "truck.png";
var REQ_PER_MIN = 10; //-1 means no limit
var mapVar = mapVar || {};

var googleAPI = new GeocoderJS.createGeocoder({'provider': 'google'});
var yandexAPI =  new GeocoderJS.createGeocoder('yandex');
var onemapAPI = new OneMapProvider();
var MapGeocoder;

/*
Create an OpenStreetMap with the following params:
div_id: id of the div element which contains the map, 
	make sure the element has a defined height
center: array to hold the geocode for the map center
level: zoom level
*/

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
    //var geocoder = L.Control.Geocoder.Google();
    
    //MAP_GEOCODER = L.Control.geocoder({geocode: geocoder}).addTo(map);
    //MAP_GEOCODER = L.Control.geocoder().addTo(map);
    //map.invalidateSize(false);
    //var marker = L.marker(center).addTo(map);
    //For Testing only
    //marker.bindPopup("<b>Testing</b><br>").openPopup();
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
function show_routes_osmap(map_opts, routes, multi_route_warning_id, color_legend_id){
    var map = create_osmap(map_opts);
    var time_delay;
    
    if (REQ_PER_MIN == -1)
        time_delay = 10;
    else
        time_delay = (1000/REQ_PER_MIN);
    
    var color_size = COLOR_ARRAY.length;
    var route_size = Object.keys(routes).length;
    if (route_size >= color_size) {
        show_item(multi_route_warning_id);
        route_size = color_size;
    }
    var map_legend_item = $(color_legend_id);
    
    
    //Make sure the map_legend is empty
    map_legend_item.empty();
    
    var out_counter = 0;
    var fleets = Object.keys(routes);
    var total_interval = time_delay * routes[fleets[0]].length;
    
    //Double recursive function to properly delay the request sent
    function outer_loop(){
        setTimeout(function(){
            //console.log("Total interval is : " + total_interval);
            if (out_counter >= route_size)
                return;
            
            var icon_color = COLOR_ARRAY[out_counter];
            var fleet_no = fleets[out_counter];
            var record = routes[fleet_no];
            var inner_counter = 0;
            var inner_max = record.length;
            
            if (inner_max >= MAX_NUM_PER_ROUTE)
                inner_max = MAX_NUM_PER_ROUTE;
            
            total_interval = time_delay * inner_max;
            
            var img_url = NUM_ICON_PATH+'/'+icon_color+'/'+TRUCK_IMG;
            map_legend_item.append('<td>' + fleet_no + '<img src='+img_url+'></td>');
            
            function inner_loop(){
                setTimeout(function(){
                    if (inner_counter >= inner_max)
                        return;
                    var icon = create_icon(icon_color, inner_counter+1);
                    var search_str
                    if (record[inner_counter].onemap_address){
                        MapGeocoder = onemapAPI;
                        search_str = record[inner_counter].onemap_address;
                    }
                    else{
                        MapGeocoder = googleAPI;
                        search_str = record[inner_counter].full_address;
                    }
                        
                    var popup_str = "Fleet: " + fleet_no + " Address: "+ search_str;
                    mark_geocode(map, search_str, icon, popup_str);
                    inner_counter++;
                    inner_loop();
                }, time_delay);
            }
            inner_loop();
            out_counter++;
            outer_loop();
        }, total_interval);
    }
    outer_loop();
    return map;
}

function mark_geocode(map, address, icon, popup_str){
    //console.log("Marking..." + address + " with icon " + icon);
    MapGeocoder.geocode(address, function(result) {
    var r = result[0];
    var marker;
        
    if (r){
        var center = [r.latitude, r.longitude];
        
        if (icon){
            marker = L.marker(center, {icon:icon}).addTo(map);
            }
        else{
             marker = L.marker(center).addTo(map);
            }
        
        if (popup_str) {
            //popup_str += " [" + r.latitude + "," + r.longitude + "]";
            marker.bindPopup(popup_str);
        }
            
        }             
    });
}

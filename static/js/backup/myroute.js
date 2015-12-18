//Overwrite the default image path for leaflet
L.Icon.Default.imagePath = '/images/leaflet';

function show_item(div_id) {
        $(div_id).show();
	}

function create_icon (color, number){
	path = L.Icon.Default.imagePath;
	icon = L.icon({
	    iconUrl:	  path+'/'+color+'/'+'number_'+number+'.png',
	    iconSize:     [25, 25], // size of the icon
	    iconAnchor:   [0, 0], // point of the icon which will correspond to marker's location
	    popupAnchor:  [2, 2] // point from which the popup should open relative to the iconAnchor
		});
	return icon;
}

function show_osm_map(){
	show_item(route_analysis)
	show_item(routemap)
	
	var map = L.map('osmmap').setView([1.382879, 103.785417], 13);
	L.tileLayer( 'http://{s}.mqcdn.com/tiles/1.0.0/map/{z}/{x}/{y}.png', {
    			attribution: '&copy; <a href="http://osm.org/copyright" title="OpenStreetMap" target="_blank">OpenStreetMap</a> contributors | Tiles Courtesy of <a href="http://www.mapquest.com/" title="MapQuest" target="_blank">MapQuest</a> <img src="http://developer.mapquest.com/content/osm/mq_logo.png" width="16" height="16">',
    			subdomains: ['otile1','otile2','otile3','otile4']
			}).addTo( map );


	L.marker([1.442879, 103.785417], {icon:create_icon("red", "1")}).addTo(map).bindPopup("Republic Polytechnic");
	L.marker([1.438454, 103.796302], {icon:create_icon("red", "2")}).addTo(map);
	L.marker([1.440717, 103.800840], {icon:create_icon("red", "3")}).addTo(map);
	L.marker([1.404421, 103.792880], {icon:create_icon("red", "4")}).addTo(map);
	L.marker([1.381898, 103.844807], {icon:create_icon("red", "5")}).addTo(map);
	L.marker([1.379238, 103.766100], {icon:create_icon("red", "6")}).addTo(map);
	L.marker([1.441532, 103.824980], {icon:create_icon("red", "7")}).addTo(map);
	
	L.marker([1.340281, 103.707049], {icon:create_icon("green", "1")}).addTo(map);
	L.marker([1.344572, 103.720181], {icon:create_icon("green", "2")}).addTo(map);
	L.marker([1.359213, 103.750179], {icon:create_icon("green", "3")}).addTo(map);
	L.marker([1.361208, 103.767946], {icon:create_icon("green", "4")}).addTo(map);
	L.marker([1.343360, 103.767205], {icon:create_icon("green", "5")}).addTo(map);
	
	/*L.Routing.control({
		waypoints: [
			L.latLng(1.442879, 103.785417),
		    L.latLng(1.438454, 103.796302),
		    L.latLng(1.440717, 103.800840),
		    L.latLng(1.404421, 103.792880),
		    L.latLng(1.381898, 103.844807),
		    L.latLng(1.379238, 103.766100),
		    L.latLng(1.441532, 103.824980)
	  		],
	  	lineOptions: {styles: [{color: 'black', opacity: 0.15, weight: 9}, {color: 'white', opacity: 0.8, weight: 6}, {color: 'blue', opacity: 1, weight: 2}]}
	}).addTo(map);

	L.Routing.control({
		waypoints: [
			L.latLng(1.340281, 103.707049),
			L.latLng(1.344572, 103.720181),
			L.latLng(1.359213, 103.750179),
			L.latLng(1.361208, 103.767946),
			L.latLng(1.343360, 103.767205)
		],
		lineOptions: {styles: [{color: 'black', opacity: 0.15, weight: 9}, {color: 'white', opacity: 0.8, weight: 6}, {color: 'red', opacity: 1, weight: 2}]}
	}).addTo(map); 
	
	
						 	<script language="JavaScript" type="text/JavaScript">
							//add map with defined center location and zoom level
        					var centerPoint = "22669.29951443939, 47171.80258283022";
        					var levelNumber = 5;
        					var OneMap = new GetOneMap('ommap', 'SM', { level: levelNumber, center: centerPoint });
    					</script>
	*/
}

/*$(document).ready(function() {
	 $('#dataTables-example').DataTable();
	
});*/
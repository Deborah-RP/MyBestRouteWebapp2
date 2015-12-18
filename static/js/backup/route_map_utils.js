/*
 * The function will find the location in the following step:
 * 1. use W3C navigator.geolocation
 * 2. if 2 fail, use a default location
 * The location will the be set to cookie
 */
$.cookie.json = true;

function set_browser_location(){
	//Step 1
	var loc = {
		lat: 1.443930,
		lng: 103.785256
	}
	
	if ($.cookie('browser_loc'))
	{
		return; 
	}
	else {
		$.cookie('browser_loc', loc);
	}
	
	var options = {
		  enableHighAccuracy: true,
		  timeout:10000,
		  maximumAge:60000
		};
	
	if(navigator.geolocation) {
	    navigator.geolocation.getCurrentPosition(function(position) {
	    	var crd = position.coords;
	    	loc.lat = crd.latitude;
	    	loc.lng = crd.longitude;
	    	$.cookie('browser_loc', loc);
	    	console.log(loc);
	    	console.log('Your current position is:');
	    	console.log('Latitude : ' + crd.latitude);
	    	console.log('Longitude: ' + crd.longitude);
	    	console.log('More or less ' + crd.accuracy + ' meters.');
	    }, null, options);
	 }
}//End of set_browser_location





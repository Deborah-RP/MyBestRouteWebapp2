"use strict";

var OneMapProvider = function() {
   this.cv = new SVY21();
};

OneMapProvider.prototype.mapToGeocoded = function (result) {
    var geocoded = new GeocoderJS.Geocoded();
    geocoded.latitude = result.Y;
    geocoded.longitude = result.X;
    //print_obj(result);
    return geocoded;
};

OneMapProvider.prototype.geocode = function (searchString, callback) {
    var basicSearch = new BasicSearch;
    var _this = this;
    
    searchString = searchString.replace(/(Singapore|singapore)/g, "");
    searchString.trim();
    basicSearch.searchVal = searchString;
    basicSearch.returnGeom = '1';
    basicSearch.GetSearchResults(function (data) {
        if (data.results == 'No results') {
            console.log("No result for " + searchString);   
            return;
        }

        var results = [];
        for (var i in data.results) {
            results.push(_this.mapToGeocoded(data.results[i]));
        }
        callback(results);
    });
};

/*
  This function return the driving direction between two or more locations.
  Input params: 
    loc_array: list of location information. 
        X and Y coordinates are separated by a comma and a pair is separated by a semi-colon. S         Set of locations can be address or postal code.
  route_data (class Route):
      routeStops: 
        The set of locations (stops) coordinates.
        X and Y coordinates are separated by a comma 
        and a pair is separated by a semi-colon
        Set of locations can be address or postal code
        A max of 9 locations can be provided.
        example: x1,y1;x2,y2;x3,y3........ OR kaki bukit road 3;307987
    routeMode: Required
        Specify the mode of transport. Default value is Drive
        Values: Drive, Cycle
    avoidERP: Required
        Use this parameter to either avoid or consider ERP locations in the result
        0 : Avoid ERP
        1 : Consider ERP
        Default:  0 
        This parameter is not applicable for Cycle Route
    routeOption:
        Use this parameter to choose Shortest or Fastest route between to stops
        Values: <String> Shortest/Fastest
        Default:  Shortest
    barriers:
        The set of barrier location coordinates. 
        X and Y coordinates are separated by a comma and a pair is separated by a semi-colon. 
        Set of locations can be address or postal code.
        Values: x1,y1;x2,y2;x3,y3
  Result {}: Object containing name value collection with directions information.
    results: ?
        message: []
        routes: {}
            fieldAliases: Set of name-value pairs for the attribute's field and alias names.
            features[]: 
                attributes {}:
                    Total_Minutes:
                    Shape_Length:?
                geometry:
                    paths: [[[X,Y], [X,Y]...]]
        directions: []
            summary:
                totalLength (km?): The length of the route.
                totalTime (mins?): The total time calculated for the route.
                totalDriveTime: Actual drive time calculated for the route.
                envelope: 
            features[]: 
                attributes:
                    length: The length of the route segment.
                    time: The time to travel along the route segment.
                    text: The direction text.
                    ETA: The estimated time of arrival at the route segment in the local time.
 */
OneMapProvider.prototype.get_direction = function(loc_array, callback){
    //Check location list length, make sure it's between 2 and 9
    var error_log = "Error at OneMapProvider.get_route : ";
    var route_result = {};
    var _this = this;
    
    if (loc_array === undefined){
        console.log(error_log + "undefined loc_array");
        callback(false);
        return;
    }
    
    if (loc_array.length < 2 || loc_array.length > 9) {
        console.log(error_log +"number of locations should between 2 and 9");
        return false;
    }
    var route_data = new Route;
    route_data.routeStops = loc_array.join(";");
    route_data.routeMode = 'Drive';
    route_data.GetRoute(function (routeResults){
        if (routeResults.results === "No results") {
                console.log(error_log + "no Route found");
                callback(false)
                return;
            }
        try {
                var tmp_paths = routeResults.results.routes.features[0].geometry.paths[0];
                route_result.paths = [];
                for (var idx = 0; idx < tmp_paths.length; idx++){
                    var tmp_p = tmp_paths[idx];
                    var tmp_r = _this.cv.computeLatLon(tmp_p[1], tmp_p[0]);
                    var tmp_coord = [tmp_r.lon, tmp_r.lat];
                    route_result.paths.push(tmp_coord);
                    }

                route_result.total_time = routeResults.results.directions[0].summary.totalTime;
                route_result.distance = routeResults.results.directions[0].summary.totalLength;
                callback(route_result);
            }
        catch(err){
                console.log(error_log + "unexpected error " + err.message);
                print_obj(loc_array);
                callback(false)
                return;
            }
    });
    return;;
}
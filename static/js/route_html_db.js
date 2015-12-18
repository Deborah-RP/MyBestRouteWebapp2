/* 
 Define the Javascript Object to store the
 the relationship between html tag and data model Plan(Close/Open/Active).
 This is mostly for rendering.
 Object structure:
 	html_tag_id
 		cls : class name
 		prop_name: property name in the class
 		full_key: the key name relative to ClosePlan (for dataTable)

For id that starts with _ means it for display only
It will not be sent to backend.
*/

var ROUTE_PLAN_HTML = {
	close_vehicle_id : {cls: "Vehicle", prop_name : "vehicle_id", full_key: "vehicle_id", column_width: "100px"},
	_date_format : {cls: "TimeWindow", prop_name: "_date_format", full_key: "none"},
	_tm_window_date: {cls: "TimeWindow", prop_name: "_tm_window_date", full_key: "task.delivery_tm_window._tm_window_date"},
	_start_tm_slot: {cls: "TimeWindow", prop_name: "_start_tm_slot", full_key: "task.delivery_tm_window._start_tm_slot"},
	_end_tm_slot: {cls: "TimeWindow", prop_name: "_end_tm_slot", full_key: "task.delivery_tm_window._end_tm_slot"},
	close_delivery_start_tm: {cls: "TimeWindow", prop_name: "start_tm", full_key: "task.delivery_tm_window.start_tm"},
	close_delivery_end_tm: {cls: "TimeWindow", prop_name: "end_tm", full_key: "task.delivery_tm_window.end_tm"},
	close_delivery_address: {cls: "Location", prop_name: "address", full_key: "task.destination.address"},
	close_delivery_country: {cls: "Location", prop_name: "country", full_key: "task.destination.country"},
	close_delivery_postal: {cls: "Location", prop_name: "postal", full_key: "task.destination.postal"},
	close_delivery_city: {cls: "Location", prop_name: "city", full_key: "task.destination.city"},
	close_delivery_state: {cls: "Location", prop_name: "state", full_key: "task.destination.state"},
	close_task_id : {cls: "Task", prop_name: "task_id", full_key: "route.task_id"},

};


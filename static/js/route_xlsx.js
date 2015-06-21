"use strict";

var pageVar = pageVar || {};

//Convert big data into string
function fix_data(data, bar, strTxt) {
	var o = "", l = 0, w = 10240, size = data.byteLength/w;
    var progress = 0;
	for(; l<size; ++l) {
        o+=String.fromCharCode.apply(null,new Uint8Array(data.slice(l*w,l*w+w)));
    }
	o+=String.fromCharCode.apply(null, new Uint8Array(data.slice(l*w)));
	return o;
}

function to_json(worksheet) {
    var result = XLSX.utils.sheet_to_row_object_array(worksheet);
    return result;
}

//Retrieve the header (first column) from worksheet
function get_header(worksheet) {
    var range =  XLSX.utils.decode_range(worksheet['!ref']);
    var header = {};
    for(var C = range.s.c; C <= range.e.c; ++C) {
        var addr = XLSX.utils.encode_cell({r:range.s.r, c:C});
        var cell = worksheet[addr];
        if(!cell) continue;
        header[C] = cell.v;
    }//End of for
    return header;
}

/*
* This function takes in worksheet output array, filter
* to produce the desired json output
* Filter format:
* name: col number in the worksheet
* if the col number is -1, the col is not selected.
*/
function filter_worksheet(sheet_output, filter, sel_by_val){
    var filtered_data = [];
    var key, val, col_name;
    
    for (var i = 0; i < sheet_output.length; i++){
        var row = {};
        for (key in filter){
            col_name = filter[key];
            val = sheet_output[i][col_name];
            if (val)
                row[key] = val;
        }
        
        for (key in sel_by_val) {
            val = $(sel_by_val[key]).val();
            //print_obj(sel_by_val[key]);
            row[key] = val;
            //print_obj(row[key]);
        }
            
        filtered_data.push(row);
    }
    return filtered_data;
}
/*
* This function takes in the filtered worksheet data
* and create and Plan object for mapping
*/
function create_close_plan(filtered_data){
    var _vehicle_id_array = [];
    var fleet = [];
    var _dt_form = [];
    
    for (var idx = 0; idx < filtered_data.length; idx++){
        var tm_window = new TimeWindow(filtered_data[idx]);
        var location = new Location(filtered_data[idx]);
        var task = new Task(filtered_data[idx]);
        task.set_destination(location);
        task.set_delivery_tm_window(tm_window);
        var vehicle = new Vehicle(filtered_data[idx]);
        
        //Check if the vehicle is already in the plan
        var v_idx = $.inArray(vehicle.vehicle_id, _vehicle_id_array);
        
        //New route
        if (v_idx === -1) {
            _vehicle_id_array.push(vehicle.vehicle_id);
            var new_route = [];
            vehicle.set_route(new_route);
            fleet.push(vehicle);
            v_idx = _vehicle_id_array.length - 1;
        }
        
        //Add the task into the vehicle's route
        fleet[v_idx].add_task(task);
        
        var _dt_obj = {};
        _dt_obj.vehicle_id = vehicle.vehicle_id;
        _dt_obj.task = task;
        _dt_form.push(_dt_obj);
    }
    
    for (var idx = 0; idx < fleet.length; idx++){
        //Sort each vehicle's route by timestamp
        fleet[idx].sort_route_by_delivery_tm();   
    }
    var close_plan = new ClosedPlan(fleet);
    close_plan.set_dt_form(_dt_form);
    return close_plan;
}

/*
* This function takes in the filter worksheet data
* and create the json object for mapping
*/
/*function create_map_json(filtered_data){
    var map_json = [];
    for (var idx = 0; idx < filtered_data.length; idx++){
        var tm_window = new TimeWindow(filtered_data[idx])
        var fleet = new Fleet(filtered_data[idx]);
        var location = new Location(filtered_data[idx]);
        var tmp_obj = {};
        tmp_obj[TimeWindow.key_name] = tm_window;
        tmp_obj[Fleet.key_name] = fleet;
        tmp_obj[Location.key_name] = location;
        map_json.push(tmp_obj);
    }
	print_obj(map_json);
    return map_json;
}*/

/*
* This function accept the whole data set
* and filter the data based on selected date & time
*/
/*function filter_route_by_dt(sheet_data, start_tm, end_tm){
    var route_data = {};
    for (var idx = 0; idx < sheet_data.length; idx++){
        var record = sheet_data[idx];
        if ( record.tm_window.end_tm < start_tm || 
             record.tm_window.start_tm > end_tm
           )
            continue;
        var key = record.fleet.fleet_no;
        if ( key in route_data){
            route_data[key].push(record.location);
        }
        else {
            route_data[key] = [];
            route_data[key].push(record.location);
        }
    }
    return route_data;
}*/

function process_workbook(workbook, ignore_headers){
    //Get the first worksheet content
    var first_name = workbook.SheetNames[0];
    var first_sheet = workbook.Sheets[first_name];
    
    //Get the header information from the firstworksheet
    var xlf_header = get_header(first_sheet);

    //Add the header to select options, skip those in the ignore list
    add_select_options(xlf_header, ignore_headers);
    var output = to_json(first_sheet);
    return output;
}

function handleMap(e){
    ga('send', 'event', 'button', 'click', 'mapBtn');
    //Read date and time
    var sel_date = $(e.data.selected_date_id).val();
    var sel_start_tm = $(e.data.selected_start_tm_id).val();
    var sel_end_tm = $(e.data.selected_end_tm_id).val();
    var start_tm = covert_to_second(sel_date, sel_start_tm);
    var end_tm = covert_to_second(sel_date, sel_end_tm);
    
    if (end_tm < start_tm){
      alert("Please make sure the end time is not earlier than start time!");
      return;
    }
    show_item(e.data.map_panel_id);
    
    var route_data = pageVar.closed_plan.get_fleet();
    
    for (var idx = 0; idx < route_data.length; idx++){
        route_data[idx].filter_route_by_delivery_tm(start_tm, end_tm);
    }
    
    var map_opts = {
		  div_id: e.data.map_div_id,
		  //center: [1.443930, 103.785256],
		  zoom : e.data.map_zoom_level, 
        };
    var new_plan = new ClosedPlan(route_data);
    show_routes_osmap(map_opts, new_plan, e.data.multi_route_warning_id, e.data.color_legend_id);
}

function handleClickConfirm(e){
    if (e.data.dt_table_bar_id) {
        var dt_table_bar = $(e.data.dt_table_bar_id);
        update_progress_bar(dt_table_bar, 65, "Processing Data", "progress-bar-warning progress-bar-striped");
    }
    
    var filter = get_select_text();
    var filtered_data = filter_worksheet(e.data.output, filter, e.data.sel_by_val);
    var closed_plan = create_close_plan(filtered_data);
    var tb_data = closed_plan.get_dt_form();
    pageVar.closed_plan = closed_plan;
    
    show_item(e.data.route_data_id);
    var tb_header = get_select_label(e.data.ignore_headers);
    display_dataTable(e.data.data_table_id, tb_data, tb_header);
    update_progress_bar(dt_table_bar, 100, "Processed data ", "progress-bar-info");
    show_item(e.data.map_filter_panel_id);
    
    var date_val = tb_data[0].task.delivery_tm_window._tm_window_date;
    $(e.data.selected_date_id).val(date_val);
}


//HTML5 drag-and-drop and file select using readAsArrayBuffer
function handleDropSelect(e) {
    var files, f;
    
    ga('send', 'event', 'button', 'click', 'drop_select');

    if (e.data.m_sheet_warning_id) {
        hide_item(e.data.m_sheet_warning_id);
    }
    
    if (e.type === 'drop' || e.type === 'q_drop_f') {
        e.stopPropagation();
        e.preventDefault();
        files = e.originalEvent.dataTransfer.files;
    }
    
    if (e.type === 'change'){
        files = e.originalEvent.target.files;
    }
    
    f = files[0];
    
    if (e.data.read_bar_id) {
        var read_bar = $(e.data.read_bar_id);
        var bar_text ="Reading data from " + f.name + "......";
        update_progress_bar(read_bar, 65, bar_text, "progress-bar-warning progress-bar-striped");
    }
  
    var reader = new FileReader();
    
    reader.onload = function(event) {
        var data = event.target.result;
        var rawStr = fix_data(data);
        
        try {
            var workbook = XLSX.read(btoa(rawStr), {type: 'base64'});
            
            if (workbook.SheetNames.length > 1){
                show_item(e.data.m_sheet_warning_id);
            }
            
            //Read the worksheet based on the selected options
            var output = process_workbook(workbook, e.data.ignore_headers);
            
            var click_confirm_param = {
                output : output,
                dt_table_bar_id : e.data.dt_table_bar_id,
                route_data_id : e.data.route_data_id,
                ignore_headers : e.data.ignore_headers,
                data_table_id : e.data.data_table_id,
                map_filter_panel_id : e.data.map_filter_panel_id,
                selected_date_id: e.data.selected_date_id,
                sel_by_val: e.data.sel_by_val,
            }
            $(e.data.confirm_opt_id).click(click_confirm_param, handleClickConfirm);
        
            if (read_bar)
                update_progress_bar(read_bar, 100, "Read data ", "progress-bar-info");

            }   
        catch (error){
            alert(error);
        };
        
        //For qunit test
        var qunit_e = $.Event('q_drop_end',{});
        $('body').trigger(qunit_e, {output});
    };
    
    reader.readAsArrayBuffer(f);
}


function handleDragover(e) {
    //console.log("Handling drag over.");
    e.stopPropagation();
    e.preventDefault();
    //Change the css of the drap area, usually is to highlight with border
    if (e.data.obj_css_array)
        change_css(e.data.obj_css_array);
}

function handleDragenter(e) {
    e.stopPropagation();
    e.preventDefault();
}






function handleShowItem(e) {
    //console.log("showing " + e.data.show_id);
    $(e.data.show_id).show();
}

function show_item(item_id){
    $(item_id).show();   
}

function hide_item(item_id){
    $(item_id).hide();   
}

function print_obj(obj){
    console.log(JSON.stringify(obj));   
}

//Pad symbol at the beginning of string
function pad_str(old_str, symbol, str_len){
    if (old_str.length < str_len)
        return pad_str(symbol+old_str, symbol, str_len);
    else
        return old_str;
}

/*
* This function will change the css style for objects
* It will accept the below data array[]
*   obj_id: the object that need to change the css style
*   css_array: the array that contains all the css property name and value
*       name: css property name
*       value: css property value
*/

function change_css (obj_css_array) {
    if (typeof obj_css_array === "undefined") {
        console.log("undefined obj_css_array in function change_css");
        return false;
    }
    
    $.each(obj_css_array, function(obj_idx, obj) {
        if (obj.css_array === "undefined") {
            console.log("undefined css_array in function change_css");
            return;
        };
        
        var html_obj = $(obj.obj_id);
        //console.log("Changing css for " + obj.obj_id);
        
        $.each(obj.css_array, function(css_idx, css_obj) {
            html_obj.css(css_obj.name, css_obj.value);
        });
    });
    return true;
}

//Function to update the progress bar
function update_progress_bar (bar, progress, strTxt, style){
    if (typeof bar === "undefined")
        return false;
    
    bar.hide();
    bar.css('transition', 'none');
    bar.css('width', progress+'%').attr('aria-valuenow', progress); 
    
    if (style){
        bar.attr("class", "progress-bar "+style);
    }
    
    if (strTxt){
        if (progress === 100){
            bar.text(strTxt + progress + "%");
        }
        else
            bar.text(strTxt);
    }
    bar.show();
}

//Function to animate the progress bar
function animate_progress_bar(bar, strTxt){
    var progress;
    console.log("Animate progress bar is " + progress+'%');
    if (strTxt){
        bar.text(strTxt);
    }
    var animate = setInterval(function(){
        progress = parseInt(bar.attr('aria-valuenow'), 10)+1;
        if (progress >=100){
            clearInterval(animate);
        }
        bar.css('width', progress+'%').attr('aria-valuenow', progress); 
    }, 10);
}

//Function to add options to select list from an array
function add_select_options(options, ignore_list){
    var selectList = $("select");
    
    selectList.each(function(){
        //Skip the select item which id is in the ignore list
        if ($.inArray($(this).attr('id'), ignore_list) !== -1){
            //console.log("Skip " + $(this).attr('id'));
            return;
        }
        
        //Clear the select list first
        $(this).empty();
        
        $(this).append($("<option></option>")
        .attr("value",-1)
        .text("Choose the option"));  
        
        for (var key in options){
            var value = options[key];
            $(this).append($("<option> </option>")
            .attr("value",key)
            .text(value));
        }
    });
}

//Function to get all the select elements with their values
function get_select_val(){
    //console.log("Clicking...");
    var selectList = $("select");
    var tmpList = {};
    selectList.each(function(){
        var key = $(this).attr('id');
        //var val = parseInt($(this).val(), 10);
        var val = $(this).val();
        //console.log("Select " + key + ":" + val);
        if (val !== "Choose the option") {
            tmpList[key] = val;
        }
    });
    return tmpList;
}

//Function to get all the select elements with their text
function get_select_text(){
    var selectList = $("select");
    var tmpList = {};
    selectList.each(function(){
        var key = $(this).attr('id');
        //var val = parseInt($(this).val(), 10);
        var val = $(this).find("option:selected").text();
        //console.log("Select " + key + ":" + val);
        if (val !== "Choose the option") {
            tmpList[key] = val;
            //console.log("The type of key is " + (typeof key));
            //console.log("Select " + key + ":" + val + " resultList is " + tmpList);
        }
    });
    return tmpList;
}

//Function to get the select id and label
function get_select_label(ignore_list){
    var selectList = $("select");
    var tmpList = {};
    selectList.each(function(){
        var key = $(this).attr('id');
        
        if (ignore_list)
            if ($.inArray(key, ignore_list) !== -1)
                return;
        
        var val = $(this).find("option:selected").text().trim();
        if (val !== "Choose the option") 
        {
            val = $("label[for='"+ key +"']").text().trim();
            tmpList[key] = val;
        }
    });
    return tmpList;
}

//Function to cover any hh:mm string to 24 hours
function convert_to_24h(tm_str, default_tm){
    var hours, minutes, AMPM, tmp;
    minutes = 0;

    if (!tm_str)
        tm_str = default_tm;
    
    tmp = tm_str.match(/^(\d+)/);
    if (tmp){
        hours = Number(tmp[1]);
    }
    
    tmp = tm_str.match(/:(\d+)/);
    if (tmp) {
        minutes = Number(tmp[1]);
    }
    
    tmp = tm_str.match(/(AM|PM)/i);
    if (tmp) {
        AMPM = tmp[1].toUpperCase();
        if (AMPM === "PM" && hours < 12) hours = hours + 12;
        if (AMPM === "AM" && hours === 12) hours = hours - 12;
    }
    
    var sHours = hours.toString();
    var sMinutes = minutes.toString();
    if (hours < 10) sHours = "0" + sHours;
    if (minutes < 10) sMinutes = "0" + sMinutes;
    return (sHours + ":" + sMinutes);
}

//Function to convert the give date time to millisecond
function covert_to_second(date_str, tm_str){
    var tmp_str = date_str.concat(" ", tm_str);
    var tm = moment(tmp_str, "YYYY-MM-DD HH:mm").unix();
    return tm;
}

/*
* Display database with the datasource and column definition
* tb_id: the html dataTable id
* tb_data: the data source for the data
* tb_header: the key and display text for the table header
* ROUTE_PLAN_HTML: map the key to the data source structure
*/
function display_dataTable(tb_id, tb_data, tb_header){
    
    var tb_col_def =[];
    var key, table;
   
    //print_obj(tb_header);
    for (key in tb_header){
        if (key in ROUTE_PLAN_HTML){
            var tmp_obj = {};
            tmp_obj.title = tb_header[key];
            tmp_obj.data = ROUTE_PLAN_HTML[key].full_key;
            tb_col_def.push(tmp_obj);
        }
    }
    
    if ($.fn.dataTable.isDataTable(tb_id)) {
        $(tb_id).DataTable().destroy();
        // empty in case the columns change
        $(tb_id).empty();
    }
    
    $(tb_id).DataTable({
        destroy: true,
        data: tb_data,
        columns: tb_col_def,
        paging: true,
        ordering: true,
        });
    return true;
}



    

